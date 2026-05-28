from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from argo_interp.collection import CycleCollection, CycleIndex
from argo_interp.cycle import InterpolationAdapters, InterpolationModel
from argo_interp.cycle.adapter import LinearAdapter
from argo_interp.cycle.config.ModelSettings import ModelSettings
from argo_interp.cycle.domain.CycleError import CycleError
from argo_interp.cycle.domain.MeasureError import MeasureError
from argo_interp.cycle.domain.ModelMeta import ModelMeta


@dataclass
class StubAdapter:
    offset: float = 0.0
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


def test_cycle_collection_rejects_mismatched_dict_keys() -> None:
    model = _build_model(
        platform_number="5901001",
        cycle_number="1",
        direction="A",
        latitude=10.0,
        longitude=80.0,
        timestamp="2026-01-15",
        profile_pressure=(0.0, 100.0),
        temperature_offset=1.0,
        salinity_offset=10.0,
        temperature_slope=2.0,
        salinity_slope=3.0,
    )

    with pytest.raises(ValueError, match="dict keys must match model.meta.cycle_id"):
        CycleCollection(models={"wrong-id": model})


def test_cycle_collection_mask_supports_spatial_temporal_and_exclusion_filters() -> None:
    cycle_collection = _build_cycle_collection()

    spatial_mask = cycle_collection.mask(lat=(9.0, 13.0), lon=(79.0, 83.0))
    np.testing.assert_array_equal(spatial_mask, np.array([True, True, False]))

    timestamp_mask = cycle_collection.mask(timestamp=("2026-02-01", "2026-12-31"))
    np.testing.assert_array_equal(timestamp_mask, np.array([False, True, True]))

    seasonal_mask = cycle_collection.mask(cyclical_dates=("2026-12-01", "2026-01-31"))
    np.testing.assert_array_equal(seasonal_mask, np.array([True, False, True]))

    exclude_ids_mask = cycle_collection.mask(exclude_cycle_ids=["5901001-2-A"])
    np.testing.assert_array_equal(exclude_ids_mask, np.array([True, False, True]))

    exclude_platform_mask = cycle_collection.mask(exclude_platform_number="5901001")
    np.testing.assert_array_equal(exclude_platform_mask, np.array([False, False, True]))


def test_cycle_collection_index_and_filter_select_expected_cycles() -> None:
    cycle_collection = _build_cycle_collection()
    mask = np.array([True, False, True])

    cycle_index = cycle_collection.index(mask)

    assert isinstance(cycle_index, CycleIndex)
    np.testing.assert_array_equal(cycle_index.cycle_id, np.array(["5901001-1-A", "5902002-1-D"]))

    filtered = cycle_collection.filter(lat=(9.0, 13.0), lon=(79.0, 83.0))
    assert isinstance(filtered, CycleCollection)
    assert len(filtered) == 2
    np.testing.assert_array_equal(
        filtered.index().cycle_id,
        np.array(["5901001-1-A", "5901001-2-A"]),
    )

    filtered_dict = cycle_collection.filter(
        exclude_platform_number="5901001",
        return_models_dict=True,
    )
    assert set(filtered_dict) == {"5902002-1-D"}


def test_cycle_collection_validate_mask_shape_and_length() -> None:
    cycle_collection = _build_cycle_collection()

    with pytest.raises(ValueError, match="one-dimensional"):
        cycle_collection.index(mask=np.array([[True, False, True]]))

    with pytest.raises(ValueError, match="mask length must match"):
        cycle_collection.index(mask=np.array([True, False]))


def test_cycle_collection_interpolate_and_interp_error_return_cycle_batch() -> None:
    cycle_collection = _build_cycle_collection()
    pressure = np.array([1.0, 2.0])
    mask = np.array([True, False, True])

    interpolated = cycle_collection.interpolate(pressure, mask=mask)
    np.testing.assert_array_equal(interpolated.pressure, pressure)
    pd.testing.assert_index_equal(
        interpolated.cycle_ids,
        pd.Index(["5901001-1-A", "5902002-1-D"]),
    )
    np.testing.assert_array_equal(
        interpolated.temperature.to_numpy(),
        np.array([[2.0, 4.0], [3.0, 5.0]]),
    )
    np.testing.assert_array_equal(
        interpolated.salinity.to_numpy(),
        np.array([[11.0, 31.0], [12.0, 32.0]]),
    )

    interp_error = cycle_collection.interp_error(pressure, mask=mask)
    np.testing.assert_allclose(
        interp_error.temperature.to_numpy(),
        np.array(
            [
                [np.sqrt(0.3**2 + 0.4**2 + 1.0**2), np.sqrt(0.2**2 + 0.2**2 + 0.25**2)],
                [np.sqrt(0.3**2 + 0.4**2 + 1.0**2), np.sqrt(0.2**2 + 0.2**2 + 0.25**2)],
            ]
        ),
    )
    np.testing.assert_allclose(
        interp_error.salinity.to_numpy(),
        np.array(
            [
                [np.sqrt(0.1**2 + 0.2**2 + 1.5**2), np.sqrt(0.3**2 + 0.1**2 + 2.5**2)],
                [np.sqrt(0.1**2 + 0.2**2 + 1.5**2), np.sqrt(0.3**2 + 0.1**2 + 2.5**2)],
            ]
        ),
    )


def test_cycle_collection_interpolate_returns_empty_frames_for_empty_selection() -> None:
    cycle_collection = _build_cycle_collection()
    pressure = np.array([1.0, 2.0])

    result = cycle_collection.interpolate(pressure, mask=np.array([False, False, False]))

    pd.testing.assert_index_equal(result.temperature.index, pd.Index(pressure, name="pressure"))
    pd.testing.assert_index_equal(result.salinity.index, pd.Index(pressure, name="pressure"))
    assert result.temperature.empty
    assert result.salinity.empty


def test_cycle_collection_metadata_warns_and_matches_index_frame() -> None:
    cycle_collection = _build_cycle_collection()

    with pytest.deprecated_call(match="CycleCollection.metadata is deprecated"):
        metadata_frame = cycle_collection.metadata

    pd.testing.assert_frame_equal(metadata_frame, cycle_collection.index().to_frame())


def test_cycle_collection_pop_removes_model_and_rebuilds_index() -> None:
    cycle_collection = _build_cycle_collection()

    removed = cycle_collection.pop("5901001-2-A")

    assert removed.meta.cycle_id == "5901001-2-A"
    assert len(cycle_collection) == 2
    np.testing.assert_array_equal(
        cycle_collection.index().cycle_id,
        np.array(["5901001-1-A", "5902002-1-D"]),
    )


def test_cycle_collection_from_dataset_builds_models_by_cycle() -> None:
    dataset = _build_cycle_dataset()

    cycle_collection = CycleCollection.from_dataset(
        dataset,
        adapter=LinearAdapter,
        settings=ModelSettings(n_folds=1),
        min_points=3,
    )

    assert len(cycle_collection) == 2
    index = cycle_collection.index()
    np.testing.assert_array_equal(index.cycle_id, np.array(["5901001-1-A", "5902002-1-D"]))
    np.testing.assert_array_equal(index.pressure_min, np.array([0.0, 10.0]))
    np.testing.assert_array_equal(index.pressure_max, np.array([20.0, 30.0]))

    interpolated = cycle_collection.interpolate([5.0, 15.0])
    np.testing.assert_allclose(
        interpolated.temperature["5901001-1-A"].to_numpy(),
        np.array([10.5, 11.5]),
    )

    interpolated = cycle_collection.interpolate([15.0, 25.0])
    np.testing.assert_allclose(
        interpolated.salinity["5902002-1-D"].to_numpy(),
        np.array([36.5, 37.5]),
    )


def test_cycle_collection_from_dataset_skips_cycles_below_min_points() -> None:
    cycle_collection = CycleCollection.from_dataset(
        _build_cycle_dataset(),
        adapter=LinearAdapter,
        settings=ModelSettings(n_folds=2),
        min_points=4,
    )

    assert len(cycle_collection) == 0


def test_cycle_collection_from_dataset_updates_progress_bar() -> None:
    pbar = StubProgressBar()

    CycleCollection.from_dataset(
        _build_cycle_dataset(),
        adapter=LinearAdapter,
        settings=ModelSettings(n_folds=1),
        min_points=3,
        pbar=pbar,
    )

    assert pbar.count == 2
    assert pbar.total == 2


def test_cycle_collection_from_dataset_rejects_missing_required_variables() -> None:
    dataset = _build_cycle_dataset().drop_vars("PSAL")

    with pytest.raises(ValueError, match="missing required variables"):
        CycleCollection.from_dataset(
            dataset,
            adapter=LinearAdapter,
            settings=ModelSettings(n_folds=2),
        )


def test_cycle_collection_from_dataset_rejects_invalid_validation_settings() -> None:
    with pytest.raises(ValueError, match="n_folds cannot exceed"):
        CycleCollection.from_dataset(
            _build_cycle_dataset(),
            adapter=LinearAdapter,
            settings=ModelSettings(n_folds=2),
            min_points=3,
        )


def _build_cycle_collection() -> CycleCollection:
    models = [
        _build_model(
            platform_number="5901001",
            cycle_number="1",
            direction="A",
            latitude=10.0,
            longitude=80.0,
            timestamp="2026-01-15",
            profile_pressure=(0.0, 100.0),
            temperature_offset=1.0,
            salinity_offset=10.0,
            temperature_slope=2.0,
            salinity_slope=3.0,
            temperature_error=MeasureError(sensor=0.4, model=0.3),
            salinity_error=MeasureError(sensor=0.2, model=0.1),
        ),
        _build_model(
            platform_number="5901001",
            cycle_number="2",
            direction="A",
            latitude=12.0,
            longitude=82.0,
            timestamp="2026-03-01",
            profile_pressure=(5.0, 120.0),
            temperature_offset=2.0,
            salinity_offset=20.0,
            temperature_slope=1.0,
            salinity_slope=4.0,
            temperature_error=MeasureError(sensor=0.3, model=0.2),
            salinity_error=MeasureError(sensor=0.3, model=0.2),
        ),
        _build_model(
            platform_number="5902002",
            cycle_number="1",
            direction="D",
            latitude=20.0,
            longitude=90.0,
            timestamp="2026-12-20",
            profile_pressure=(10.0, 150.0),
            temperature_offset=3.0,
            salinity_offset=30.0,
            temperature_slope=0.5,
            salinity_slope=5.0,
            temperature_error=MeasureError(sensor=0.2, model=0.2),
            salinity_error=MeasureError(sensor=0.1, model=0.3),
        ),
    ]
    return CycleCollection(models={model.meta.cycle_id: model for model in models})


def _build_cycle_dataset() -> xr.Dataset:
    return xr.Dataset(
        {
            "PLATFORM_NUMBER": ("N_POINTS", np.array(["5901001"] * 3 + ["5902002"] * 3)),
            "CYCLE_NUMBER": ("N_POINTS", np.array([1, 1, 1, 1, 1, 1])),
            "DIRECTION": ("N_POINTS", np.array(["A", "A", "A", "D", "D", "D"])),
            "LATITUDE": ("N_POINTS", np.array([10.0, 10.0, 10.0, 20.0, 20.0, 20.0])),
            "LONGITUDE": ("N_POINTS", np.array([80.0, 80.0, 80.0, 90.0, 90.0, 90.0])),
            "TIME": (
                "N_POINTS",
                np.array(["2026-01-15"] * 3 + ["2026-02-20"] * 3, dtype="datetime64[ns]"),
            ),
            "PRES": ("N_POINTS", np.array([0.0, 10.0, 20.0, 10.0, 20.0, 30.0])),
            "TEMP": ("N_POINTS", np.array([10.0, 11.0, 12.0, 21.0, 22.0, 23.0])),
            "PSAL": ("N_POINTS", np.array([35.0, 35.5, 36.0, 36.0, 37.0, 38.0])),
        }
    )


def _build_model(
    *,
    platform_number: str,
    cycle_number: str,
    direction: str,
    latitude: float,
    longitude: float,
    timestamp: str,
    profile_pressure: tuple[float, float],
    temperature_offset: float,
    salinity_offset: float,
    temperature_slope: float,
    salinity_slope: float,
    temperature_error: MeasureError | None = None,
    salinity_error: MeasureError | None = None,
) -> InterpolationModel:
    if temperature_error is None:
        temperature_error = MeasureError(sensor=0.4, model=0.3)
    if salinity_error is None:
        salinity_error = MeasureError(sensor=0.2, model=0.1)

    return InterpolationModel(
        meta=ModelMeta(
            platform_number=platform_number,
            cycle_number=cycle_number,
            direction=direction,
            latitude=latitude,
            longitude=longitude,
            timestamp=np.datetime64(timestamp),
            profile_pressure=profile_pressure,
        ),
        adapters=InterpolationAdapters(
            temperature=StubAdapter(offset=temperature_offset, slope=temperature_slope),
            salinity=StubAdapter(offset=salinity_offset, slope=salinity_slope),
        ),
        error=CycleError(
            pressure=0.5,
            temperature=temperature_error,
            salinity=salinity_error,
        ),
        settings=ModelSettings(n_folds=2),
    )
