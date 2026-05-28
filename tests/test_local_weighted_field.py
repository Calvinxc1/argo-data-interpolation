from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest

from argo_interp.collection import CycleCollection
from argo_interp.cycle import InterpolationAdapters, InterpolationModel
from argo_interp.cycle.config import ModelSettings
from argo_interp.cycle.domain import CycleError, MeasureError, ModelData, ModelMeta
from argo_interp.field import FieldProfile, FieldQuery, LocalWeightedField


@dataclass
class StubAdapter:
    offset: float
    slope: float = 0.0

    def interpolate(self, pressure_data: np.ndarray) -> np.ndarray:
        pressure = np.asarray(pressure_data, dtype=float)
        return pressure + self.offset

    def gradient(self, pressure_data: np.ndarray) -> np.ndarray:
        pressure = np.asarray(pressure_data, dtype=float)
        return np.full_like(pressure, self.slope, dtype=float)


@dataclass
class StubProgressBar:
    count: int = 0
    total: int | None = None

    def update(self, n: int = 1) -> None:
        self.count += n

    def refresh(self) -> None:
        pass


def test_local_weighted_field_interpolates_depth_aware_weighted_profile() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )

    profile = field.interpolate((0.0, 0.0, "2026-01-01", np.array([10.0, 60.0])))

    assert isinstance(profile, FieldProfile)
    assert profile.shape == (2,)
    np.testing.assert_array_equal(profile.query_index, np.array([0, 0]))
    np.testing.assert_array_equal(profile.latitude, np.array([0.0, 0.0]))
    np.testing.assert_array_equal(profile.longitude, np.array([0.0, 0.0]))
    np.testing.assert_array_equal(
        profile.timestamp,
        np.array(["2026-01-01", "2026-01-01"], dtype="datetime64[ns]"),
    )
    np.testing.assert_array_equal(profile.pressure, np.array([10.0, 60.0]))
    np.testing.assert_array_equal(profile.support_count, np.array([2, 1]))

    weights = np.exp(-0.5 * np.square(np.array([0.0, _km_per_degree_lon_at_equator()]) / 500.0))
    normalized = weights / weights.sum()
    assert profile.temperature[0] == normalized[0] * 11.0 + normalized[1] * 31.0
    assert profile.salinity[0] == normalized[0] * 110.0 + normalized[1] * 301.0
    assert profile.temperature[1] == 61.0
    assert profile.salinity[1] == 160.0


def test_field_profile_converts_to_frame_with_query_labels() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )

    profile = field.interpolate(FieldQuery(0.0, 0.0, "2026-01-01", [10.0, 60.0]))

    frame = profile.to_frame()

    assert list(frame.columns) == [
        "query_index",
        "latitude",
        "longitude",
        "timestamp",
        "pressure",
        "temperature",
        "salinity",
        "temperature_error",
        "salinity_error",
        "temperature_cycle_error",
        "salinity_cycle_error",
        "temperature_field_error",
        "salinity_field_error",
        "temperature_model_error",
        "salinity_model_error",
        "support_count",
        "support_weight",
    ]
    np.testing.assert_array_equal(frame["latitude"].to_numpy(), np.array([0.0, 0.0]))
    np.testing.assert_array_equal(frame["longitude"].to_numpy(), np.array([0.0, 0.0]))
    pd.testing.assert_series_equal(
        frame["timestamp"],
        pd.Series(np.array(["2026-01-01", "2026-01-01"], dtype="datetime64[ns]"), name="timestamp"),
    )
    np.testing.assert_array_equal(frame["pressure"].to_numpy(), np.array([10.0, 60.0]))


def test_field_profile_accepts_tuple_queries_with_different_pressure_grids() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )
    profile = field.interpolate([
        (0.0, 0.0, "2026-01-01", [10.0, 20.0]),
        (0.0, 1.0, "2026-01-01", [30.0]),
    ])

    frame = profile.to_frame()

    assert len(frame) == 3
    np.testing.assert_array_equal(frame["query_index"].to_numpy(), np.array([0, 0, 1]))
    assert set(frame["longitude"]) == {0.0, 1.0}
    assert set(frame["pressure"]) == {10.0, 20.0, 30.0}


def test_field_profile_to_frame_preserves_duplicate_coordinate_records() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )
    profile = field.interpolate([
        (0.0, 0.0, "2026-01-01", [10.0, 20.0]),
        (0.0, 1.0, "2026-01-01", [10.0, 20.0]),
    ])

    frame = profile.to_frame()

    assert len(frame) == profile.shape[0]
    assert len(frame[["latitude", "longitude", "timestamp", "pressure"]].drop_duplicates()) == 4
    np.testing.assert_array_equal(frame["query_index"].to_numpy(), np.array([0, 0, 1, 1]))


def test_field_profile_to_frame_preserves_flat_records() -> None:
    values = np.arange(3, dtype=float)
    profile = FieldProfile(
        query_index=np.array([0, 1, 1]),
        latitude=np.array([7.0, 7.5, 7.5]),
        longitude=np.array([80.5, 81.0, 81.0]),
        timestamp=np.array(["2017-01-01", "2017-01-02", "2017-01-02"], dtype="datetime64[ns]"),
        pressure=np.array([10.0, 10.0, 20.0]),
        temperature=values,
        salinity=values,
        temperature_error=values,
        salinity_error=values,
        temperature_cycle_error=values,
        salinity_cycle_error=values,
        temperature_field_error=values,
        salinity_field_error=values,
        temperature_model_error=values,
        salinity_model_error=values,
        support_count=values.astype(int),
        support_weight=values,
    )

    frame = profile.to_frame()

    assert len(frame) == 3
    assert set(frame["latitude"]) == {7.0, 7.5}
    assert set(frame["longitude"]) == {80.5, 81.0}


def test_local_weighted_field_propagates_errors_with_normalized_weights() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )

    profile = field.interpolate((0.0, 0.0, "2026-01-01", [10.0]))

    weights = np.exp(-0.5 * np.square(np.array([0.0, _km_per_degree_lon_at_equator()]) / 500.0))
    normalized = weights / weights.sum()
    temperature_values = np.array([11.0, 31.0])
    salinity_values = np.array([110.0, 301.0])
    temperature_mean = np.sum(normalized * temperature_values)
    salinity_mean = np.sum(normalized * salinity_values)
    expected_temperature_cycle_variance = (normalized[0] * 0.5) ** 2 + (normalized[1] * 1.0) ** 2
    expected_salinity_cycle_variance = (normalized[0] * 0.25) ** 2 + (normalized[1] * 0.75) ** 2
    expected_temperature_field_variance = np.sum(
        normalized * np.square(temperature_values - temperature_mean)
    )
    expected_salinity_field_variance = np.sum(
        normalized * np.square(salinity_values - salinity_mean)
    )
    expected_temperature_cycle_error = np.sqrt(expected_temperature_cycle_variance)
    expected_salinity_cycle_error = np.sqrt(expected_salinity_cycle_variance)
    expected_temperature_field_error = np.sqrt(expected_temperature_field_variance)
    expected_salinity_field_error = np.sqrt(expected_salinity_field_variance)
    expected_temperature_error = np.sqrt(
        expected_temperature_cycle_variance + expected_temperature_field_variance
    )
    expected_salinity_error = np.sqrt(
        expected_salinity_cycle_variance + expected_salinity_field_variance
    )

    np.testing.assert_allclose(
        profile.temperature_error,
        np.array([expected_temperature_error]),
    )
    np.testing.assert_allclose(
        profile.salinity_error,
        np.array([expected_salinity_error]),
    )
    np.testing.assert_allclose(
        profile.temperature_cycle_error,
        np.array([expected_temperature_cycle_error]),
    )
    np.testing.assert_allclose(
        profile.salinity_cycle_error,
        np.array([expected_salinity_cycle_error]),
    )
    np.testing.assert_allclose(
        profile.temperature_field_error,
        np.array([expected_temperature_field_error]),
    )
    np.testing.assert_allclose(
        profile.salinity_field_error,
        np.array([expected_salinity_field_error]),
    )
    np.testing.assert_array_equal(profile.temperature_model_error, np.array([0.0]))
    np.testing.assert_array_equal(profile.salinity_model_error, np.array([0.0]))


def test_local_weighted_field_adds_model_error_in_quadrature() -> None:
    model_error = ModelData(
        pressure=np.array([10.0]),
        temperature=np.array([2.0]),
        salinity=np.array([3.0]),
    )
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    ).with_model_error(model_error)

    profile = field.interpolate((0.0, 0.0, "2026-01-01", [10.0]))

    expected_temperature_without_model = profile.temperature_cycle_error[0] ** 2
    expected_temperature_without_model += profile.temperature_field_error[0] ** 2
    expected_salinity_without_model = profile.salinity_cycle_error[0] ** 2
    expected_salinity_without_model += profile.salinity_field_error[0] ** 2

    np.testing.assert_array_equal(profile.temperature_model_error, np.array([2.0]))
    np.testing.assert_array_equal(profile.salinity_model_error, np.array([3.0]))
    np.testing.assert_allclose(
        profile.temperature_error,
        np.array([np.sqrt(expected_temperature_without_model + 2.0**2)]),
    )
    np.testing.assert_allclose(
        profile.salinity_error,
        np.array([np.sqrt(expected_salinity_without_model + 3.0**2)]),
    )


def test_local_weighted_field_cross_validates_held_out_cycles() -> None:
    field = LocalWeightedField(
        _build_three_cycle_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )

    model_error = field.cross_validate([10.0], n_folds=1)

    np.testing.assert_array_equal(model_error.pressure, np.array([10.0]))
    assert model_error.temperature.shape == (1,)
    assert model_error.salinity.shape == (1,)
    assert np.isfinite(model_error.temperature[0])
    assert np.isfinite(model_error.salinity[0])
    assert model_error.temperature[0] >= 0.0
    assert model_error.salinity[0] >= 0.0


def test_local_weighted_field_cross_validation_updates_progress_bar() -> None:
    field = LocalWeightedField(
        _build_three_cycle_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )
    pbar = StubProgressBar()

    field.cross_validate([10.0], n_folds=1, pbar=pbar)

    assert pbar.count == 1
    assert pbar.total == 1


def test_local_weighted_field_interpolates_multiple_field_queries() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )

    profile = field.interpolate([
        FieldQuery(0.0, 0.0, "2026-01-01", [10.0, 20.0]),
        FieldQuery(0.0, 1.0, "2026-01-01", [10.0, 20.0]),
    ])

    assert isinstance(profile, FieldProfile)
    assert profile.shape == (4,)
    np.testing.assert_array_equal(profile.query_index, np.array([0, 0, 1, 1]))
    np.testing.assert_array_equal(profile.latitude, np.array([0.0, 0.0, 0.0, 0.0]))
    np.testing.assert_array_equal(profile.longitude, np.array([0.0, 0.0, 1.0, 1.0]))
    np.testing.assert_array_equal(
        profile.timestamp,
        np.array(["2026-01-01"] * 4, dtype="datetime64[ns]"),
    )
    assert profile.temperature[0] < profile.temperature[2]
    assert profile.salinity[0] < profile.salinity[2]


def test_local_weighted_field_accepts_single_field_query() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=1,
    )

    profile = field.interpolate(FieldQuery(0.0, 0.0, "2026-01-01", [10.0]))

    assert isinstance(profile, FieldProfile)
    assert profile.shape == (1,)


def test_local_weighted_field_requires_minimum_depth_support() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=500.0,
        spatial_radius_km=1000.0,
        min_support=2,
    )

    profile = field.interpolate((0.0, 0.0, "2026-01-01", [10.0, 60.0]))

    assert np.isfinite(profile.temperature[0])
    assert np.isnan(profile.temperature[1])
    np.testing.assert_array_equal(profile.support_count, np.array([2, 1]))


def test_local_weighted_field_returns_empty_profile_when_no_cycles_match() -> None:
    field = LocalWeightedField(
        _build_collection(),
        spatial_scale_km=100.0,
        spatial_radius_km=10.0,
    )

    profile = field.interpolate((0.0, 0.5, "2026-01-01", [10.0, 20.0]))

    np.testing.assert_array_equal(profile.support_count, np.array([0, 0]))
    np.testing.assert_array_equal(profile.support_weight, np.array([0.0, 0.0]))
    assert np.isnan(profile.temperature).all()
    assert np.isnan(profile.salinity_error).all()


def test_local_weighted_field_rejects_invalid_configuration() -> None:
    collection = _build_collection()

    try:
        LocalWeightedField(collection, spatial_scale_km=0.0)
    except ValueError as exc:
        assert "spatial_scale_km" in str(exc)
    else:
        raise AssertionError("expected invalid spatial scale to raise")


def test_local_weighted_field_rejects_out_of_domain_location() -> None:
    field = LocalWeightedField(_build_collection(), spatial_scale_km=500.0)

    with pytest.raises(ValueError, match="latitude must be within collection bounds"):
        field.interpolate((-1.0, 0.0, "2026-01-01", [10.0]))

    with pytest.raises(ValueError, match="longitude must be within collection bounds"):
        field.interpolate((0.0, 2.0, "2026-01-01", [10.0]))


def test_local_weighted_field_rejects_out_of_domain_timestamp() -> None:
    field = LocalWeightedField(_build_collection(), spatial_scale_km=500.0)

    with pytest.raises(ValueError, match="timestamp must be within collection bounds"):
        field.interpolate((0.0, 0.0, "2025-12-31", [10.0]))


def _km_per_degree_lon_at_equator() -> float:
    return 111.1950802335329


def _build_collection() -> CycleCollection:
    models = [
        _build_model(
            cycle_number="1",
            latitude=0.0,
            longitude=0.0,
            profile_pressure=(0.0, 100.0),
            temperature_offset=1.0,
            salinity_offset=100.0,
            temperature_error=MeasureError(sensor=0.0, model=0.5),
            salinity_error=MeasureError(sensor=0.0, model=0.25),
        ),
        _build_model(
            cycle_number="2",
            latitude=0.0,
            longitude=1.0,
            profile_pressure=(0.0, 50.0),
            temperature_offset=21.0,
            salinity_offset=291.0,
            temperature_error=MeasureError(sensor=0.0, model=1.0),
            salinity_error=MeasureError(sensor=0.0, model=0.75),
        ),
    ]
    return CycleCollection(models={model.meta.cycle_id: model for model in models})


def _build_three_cycle_collection() -> CycleCollection:
    models = [
        _build_model(
            cycle_number="1",
            latitude=0.0,
            longitude=0.0,
            profile_pressure=(0.0, 100.0),
            temperature_offset=1.0,
            salinity_offset=100.0,
            temperature_error=MeasureError(sensor=0.0, model=0.5),
            salinity_error=MeasureError(sensor=0.0, model=0.25),
        ),
        _build_model(
            cycle_number="2",
            latitude=0.0,
            longitude=0.5,
            profile_pressure=(0.0, 100.0),
            temperature_offset=11.0,
            salinity_offset=200.0,
            temperature_error=MeasureError(sensor=0.0, model=0.75),
            salinity_error=MeasureError(sensor=0.0, model=0.5),
        ),
        _build_model(
            cycle_number="3",
            latitude=0.0,
            longitude=1.0,
            profile_pressure=(0.0, 100.0),
            temperature_offset=21.0,
            salinity_offset=300.0,
            temperature_error=MeasureError(sensor=0.0, model=1.0),
            salinity_error=MeasureError(sensor=0.0, model=0.75),
        ),
    ]
    return CycleCollection(models={model.meta.cycle_id: model for model in models})


def _build_model(
    *,
    cycle_number: str,
    latitude: float,
    longitude: float,
    profile_pressure: tuple[float, float],
    temperature_offset: float,
    salinity_offset: float,
    temperature_error: MeasureError,
    salinity_error: MeasureError,
) -> InterpolationModel:
    return InterpolationModel(
        meta=ModelMeta(
            platform_number="5901001",
            cycle_number=cycle_number,
            direction="A",
            latitude=latitude,
            longitude=longitude,
            timestamp=np.datetime64("2026-01-01"),
            profile_pressure=profile_pressure,
        ),
        adapters=InterpolationAdapters(
            temperature=StubAdapter(offset=temperature_offset),
            salinity=StubAdapter(offset=salinity_offset),
        ),
        error=CycleError(
            pressure=0.0,
            temperature=temperature_error,
            salinity=salinity_error,
        ),
        settings=ModelSettings(n_folds=2),
    )
