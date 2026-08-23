import numpy as np
import pandas as pd

from argo_kwsi.cycle.adapter import PchipAdapter
from argo_kwsi.cycle.config import ModelSettings
from argo_kwsi.cycle.domain import CycleError, MeasureError, ModelMeta
from argo_kwsi.cycle.model import Model
from argo_kwsi.cycle.model.ModelAdapters import ModelAdapters
from argo_kwsi.model import CycleModels
from argo_kwsi.uncertainty import (
    GaussianScale,
    SoundSpeedUncertaintyConfig,
    SoundSpeedUncertaintyProduct,
    WeightConfig,
    build_candidate_query,
    candidate_mask_for_query,
    depth_summary,
    estimate_depthwise_spatial_variance,
    great_circle_distance_km,
    seasonal_distance_seconds,
    weighted_profile_mean,
)


def test_product_query_propagates_all_variance_components() -> None:
    cycle_models = _cycle_models()
    product = SoundSpeedUncertaintyProduct(
        cycle_models=cycle_models,
        spatial_variance=_spatial_variance(),
        config=_config(),
    )

    product_result = product.query_result(latitude=10.1, longitude=80.1)
    result = product_result.data

    assert len(result) == 2
    assert result.attrs["argo_kwsi_uncertainty"] == product_result.metadata
    assert product_result.metadata["schema_version"] == "1.0"
    assert "physical-depth conversion is future work" in product_result.metadata["depth_m"]
    assert np.isfinite(result["sound_speed_teos10"]).all()
    assert np.isfinite(result["sigma_sound_speed_teos10"]).all()
    contribution_columns = [
        column for column in result.columns if column.startswith("var_sound_speed_teos10_from_")
    ]
    np.testing.assert_allclose(
        result[contribution_columns].sum(axis=1),
        result["var_sound_speed_teos10"],
    )
    np.testing.assert_allclose(
        result["var_sound_speed_teos10_sensor_bucket"]
        + result["var_sound_speed_teos10_model_bucket"],
        result["var_sound_speed_teos10"],
    )
    assert (result["candidate_cycle_count"] == 3).all()
    assert (result["effective_cycle_count"] > 0).all()


def test_product_grid_and_spatial_estimator_use_cycle_models() -> None:
    cycle_models = _cycle_models()
    spatial_variance = estimate_depthwise_spatial_variance(
        cycle_models,
        _config(),
    )
    product = SoundSpeedUncertaintyProduct(
        cycle_models=cycle_models,
        spatial_variance=spatial_variance,
        config=_config(),
    )

    batches = list(product.iter_grid_batches([10.0], [80.0, 80.2], batch_size=1))
    result = product.grid([10.0], [80.0, 80.2], batch_size=1)

    assert len(result) == 4
    assert [len(batch) for batch in batches] == [2, 2]
    assert all(batch.attrs["argo_kwsi_uncertainty"] == product.metadata() for batch in batches)
    assert set(result["pressure_dbar"]) == {5.0, 110.0}
    assert (spatial_variance["spatial_validation_count"] == 3).all()
    assert (spatial_variance["var_temperature_spatial"] > 0).all()


def test_candidate_query_and_wrapped_season_distance_validate_inputs() -> None:
    with np.testing.assert_raises(ValueError):
        build_candidate_query(target_latitude=10.0, dist_rad=1.0)

    query = build_candidate_query(
        target_latitude=10.0,
        target_longitude=80.0,
        dist_rad=1.0,
        target_timestamp=pd.Timestamp("2020-01-02"),
        season_weeks=2,
    )
    assert query.lat == (9.0, 11.0)
    assert query.lon == (79.0, 81.0)

    distance = seasonal_distance_seconds(
        np.datetime64("2020-01-01"), np.array([np.datetime64("2020-12-31")])
    )
    assert distance[0] < 2 * 24 * 60 * 60


def test_weighted_profile_mean_ignores_nonfinite_values() -> None:
    result = weighted_profile_mean(
        np.array([[1.0, np.nan, np.inf], [1.0, 3.0, 5.0]]),
        np.array([1.0, 1.0, 1.0]),
    )

    np.testing.assert_allclose(result, np.array([1.0, 3.0]))


def test_great_circle_geometry_wraps_the_antimeridian() -> None:
    cycle_models = _cycle_models()
    metadata = cycle_models.metadata()

    distances = great_circle_distance_km(
        target_latitude=10.0,
        target_longitude=179.9,
        candidate_latitude=np.array([10.0]),
        candidate_longitude=np.array([-179.9]),
    )
    mask = candidate_mask_for_query(
        metadata,
        target_latitude=10.0,
        target_longitude=80.0,
        candidate_radius=40.0,
        distance_metric="great_circle_km",
    )

    assert distances[0] < 25.0
    assert mask.sum() == 3


def test_configuration_and_product_reject_invalid_inputs() -> None:
    with np.testing.assert_raises(ValueError):
        SoundSpeedUncertaintyConfig(
            target_pressure=[5.0, 5.0],
            weight_config=_weight_config(),
            anchor_time="2020-01-01",
            candidate_radius=1.0,
        )

    with np.testing.assert_raises(ValueError):
        GaussianScale(0.0)

    with np.testing.assert_raises(ValueError):
        WeightConfig(
            distance=GaussianScale(1.0),
            time=GaussianScale(1.0),
            season=GaussianScale(1.0),
            distance_power=-1.0,
        )

    with np.testing.assert_raises(ValueError):
        SoundSpeedUncertaintyProduct(
            _cycle_models(),
            _spatial_variance().drop(columns="var_salinity_spatial"),
            _config(),
        )

    product = SoundSpeedUncertaintyProduct(_cycle_models(), _spatial_variance(), _config())
    with np.testing.assert_raises(ValueError):
        product.query(latitude=10.0, longitude=80.0, depth_indices=[0.5])


def test_empty_query_has_a_stable_schema_and_depth_summary_is_documented() -> None:
    product = SoundSpeedUncertaintyProduct(_cycle_models(), _spatial_variance(), _config())

    empty = product.query(latitude=50.0, longitude=50.0)
    summary = depth_summary(product.query(latitude=10.1, longitude=80.1))

    populated = product.query(latitude=10.1, longitude=80.1)
    assert list(empty.columns) == list(populated.columns)
    assert empty.dtypes.to_dict() == populated.dtypes.to_dict()
    assert empty.empty
    assert set(summary["depth_m"]) == {5.0, 110.0}


def test_cached_cycle_terms_are_invalidated_when_the_bundle_is_mutated() -> None:
    """A mutated bundle must not be served stale, position-indexed cached terms."""

    cycle_models = _cycle_models()
    product = SoundSpeedUncertaintyProduct(cycle_models, _spatial_variance(), _config())

    warmed = product.query(latitude=10.1, longitude=80.1)
    assert (warmed["candidate_cycle_count"] == 3).all()

    cycle_models.pop(cycle_models.metadata().cycle_id[0])
    after_mutation = product.query(latitude=10.1, longitude=80.1)

    # Ground truth: a product that never saw the pre-mutation bundle at all.
    reference = SoundSpeedUncertaintyProduct(cycle_models, _spatial_variance(), _config()).query(
        latitude=10.1, longitude=80.1
    )

    assert (after_mutation["candidate_cycle_count"] == 2).all()
    pd.testing.assert_frame_equal(after_mutation, reference)
    assert not np.allclose(warmed["temperature"], reference["temperature"])


def test_notebook6_factory_and_grid_result_expose_stable_provenance() -> None:
    config = SoundSpeedUncertaintyConfig.notebook6()
    product = SoundSpeedUncertaintyProduct(
        _cycle_models(),
        _spatial_variance(),
        _config(),
    )

    product.precompute_cycle_terms()
    result = product.grid_result([10.0], [80.0], batch_size=1)

    assert config.target_pressure == (5.0, 35.0, 110.0, 500.0)
    assert config.to_metadata()["distance_metric"] == "planar_degrees"
    assert result.metadata["cycle_model_count"] == 3
    assert result.data.attrs["argo_kwsi_uncertainty"] == result.metadata
    with np.testing.assert_raises(ValueError):
        list(product.iter_grid_batches([10.0], [80.0], batch_size=0))


def _weight_config() -> WeightConfig:
    return WeightConfig(
        distance=GaussianScale(1.0),
        time=GaussianScale(365.25 * 24 * 60 * 60),
        season=GaussianScale(365.25 * 24 * 60 * 60),
    )


def _config() -> SoundSpeedUncertaintyConfig:
    return SoundSpeedUncertaintyConfig(
        target_pressure=[5.0, 110.0],
        weight_config=_weight_config(),
        anchor_time="2020-01-15",
        candidate_radius=1.0,
        distance_metric="planar_degrees",
    )


def _spatial_variance() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "var_temperature_spatial": [0.04, 0.09],
            "var_salinity_spatial": [0.01, 0.02],
            "spatial_validation_count": [3, 3],
        },
        index=pd.Index([5.0, 110.0], name="pressure_dbar"),
    )


def _cycle_models() -> CycleModels:
    models: dict[str, Model] = {}
    pressure = np.array([0.0, 50.0, 110.0, 200.0])
    for index, offset in enumerate((0.0, 0.4, -0.3), start=1):
        temperature = np.array([28.0, 22.0, 16.0, 10.0]) + offset
        salinity = np.array([34.5, 34.8, 35.1, 35.3]) + offset / 10
        meta = ModelMeta(
            platform_number=f"59000{index}",
            cycle_number="1",
            direction="A",
            latitude=10.0 + (index - 1) * 0.1,
            longitude=80.0 + (index - 1) * 0.1,
            timestamp=np.datetime64(f"2020-01-0{index}"),
            profile_pressure=(0.0, 200.0),
        )
        model = Model(
            meta=meta,
            adapters=ModelAdapters(
                temperature=PchipAdapter.fit(pressure, temperature, {}),
                salinity=PchipAdapter.fit(pressure, salinity, {}),
            ),
            error=CycleError(
                pressure=0.2,
                temperature=MeasureError(sensor=0.01, model=0.05),
                salinity=MeasureError(sensor=0.005, model=0.01),
            ),
            settings=ModelSettings(n_folds=2),
        )
        models[meta.cycle_id] = model
    return CycleModels(models)
