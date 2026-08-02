"""Spatiotemporal Argo sound-speed uncertainty products.

This module packages the computational path developed in the Notebook 6
research product.  It accepts already-built :class:`~argo_interp.model.CycleModels`
objects, so data acquisition, cache management, plotting, and paper-specific
file paths remain outside the library API.

The propagated sound-speed variance uses the independent temperature/salinity
GUM delta-method approximation.  It deliberately omits a temperature-salinity
covariance term and the intrinsic TEOS-10 formula uncertainty.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from itertools import product
from typing import Any, Iterable, Literal

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from .acoustics import sound_speed_teos10, sound_speed_teos10_partials, sound_speed_variance
from .model import CycleData, CycleMetadata, CycleModels

AVERAGE_YEAR_SECONDS = 365.2425 * 24 * 60 * 60
DistanceMetric = Literal["planar_degrees", "great_circle_km"]

SPATIAL_VARIANCE_COLUMNS = (
    "var_temperature_spatial",
    "var_salinity_spatial",
    "spatial_validation_count",
)
PRODUCT_SCHEMA_VERSION = "1.0"
PRODUCT_COLUMNS = (
    "latitude",
    "longitude",
    "depth_m",
    "pressure_dbar",
    "timestamp_or_anchor_time",
    "temperature",
    "salinity",
    "var_temperature_sensor_precision",
    "var_temperature_pressure_gradient",
    "var_temperature_vertical_model",
    "var_temperature_spatial",
    "var_temperature_aggregate",
    "sigma_temperature_aggregate",
    "var_salinity_sensor_precision",
    "var_salinity_pressure_gradient",
    "var_salinity_vertical_model",
    "var_salinity_spatial",
    "var_salinity_aggregate",
    "sigma_salinity_aggregate",
    "sound_speed_teos10",
    "dc_teos10_dT",
    "dc_teos10_dS",
    "var_sound_speed_teos10",
    "sigma_sound_speed_teos10",
    "W_raw",
    "W_display",
    "candidate_cycle_count",
    "effective_cycle_count",
    "spatial_validation_count",
    "var_sound_speed_teos10_from_temperature_sensor_precision",
    "var_sound_speed_teos10_from_temperature_pressure_gradient",
    "var_sound_speed_teos10_from_temperature_vertical_model",
    "var_sound_speed_teos10_from_temperature_spatial",
    "var_sound_speed_teos10_from_salinity_sensor_precision",
    "var_sound_speed_teos10_from_salinity_pressure_gradient",
    "var_sound_speed_teos10_from_salinity_vertical_model",
    "var_sound_speed_teos10_from_salinity_spatial",
    "var_sound_speed_teos10_sensor_bucket",
    "var_sound_speed_teos10_model_bucket",
)


@dataclass(frozen=True, slots=True)
class GaussianScale:
    """A Gaussian kernel scale expressed in the units of its input delta."""

    sigma: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.sigma) or self.sigma <= 0:
            raise ValueError("sigma must be a positive finite number")

    @classmethod
    def from_border(cls, border: float, border_stdev: float) -> "GaussianScale":
        if not np.isfinite(border_stdev) or border_stdev <= 0:
            raise ValueError("border_stdev must be a positive finite number")
        return cls(sigma=border / border_stdev)

    def weight(self, delta: ArrayLike) -> NDArray[np.float64]:
        scaled_delta = np.asarray(delta, dtype=float) / self.sigma
        return np.exp(-0.5 * np.square(scaled_delta))


@dataclass(frozen=True, slots=True)
class WeightDeltas:
    """Distance, time, and wrapped-season differences for candidate cycles."""

    distance: NDArray[np.float64]
    time: NDArray[np.float64]
    season: NDArray[np.float64]

    def __post_init__(self) -> None:
        sizes = {self.distance.size, self.time.size, self.season.size}
        if len(sizes) != 1:
            raise ValueError("weight delta arrays must have the same size")


@dataclass(frozen=True, slots=True)
class WeightComponents:
    """Individual kernel components before they are multiplied together."""

    distance: NDArray[np.float64]
    time: NDArray[np.float64]
    season: NDArray[np.float64]

    def joint(self) -> NDArray[np.float64]:
        return self.distance * self.time * self.season


@dataclass(frozen=True, slots=True)
class WeightConfig:
    """Gaussian weighting configuration for a spatiotemporal query."""

    distance: GaussianScale
    time: GaussianScale
    season: GaussianScale
    use_distance: bool = True
    use_time: bool = True
    use_season: bool = True
    distance_power: float = 1.0
    time_power: float = 1.0
    season_power: float = 1.0

    def __post_init__(self) -> None:
        powers = (self.distance_power, self.time_power, self.season_power)
        if any(not np.isfinite(power) or power < 0 for power in powers):
            raise ValueError("weight powers must be finite, non-negative numbers")

    def component_weights(self, deltas: WeightDeltas) -> WeightComponents:
        size = deltas.distance.size
        return WeightComponents(
            distance=(
                np.power(self.distance.weight(deltas.distance), self.distance_power)
                if self.use_distance
                else np.ones(size, dtype=float)
            ),
            time=(
                np.power(self.time.weight(deltas.time), self.time_power)
                if self.use_time
                else np.ones(size, dtype=float)
            ),
            season=(
                np.power(self.season.weight(deltas.season), self.season_power)
                if self.use_season
                else np.ones(size, dtype=float)
            ),
        )

    def joint_weight(self, deltas: WeightDeltas) -> NDArray[np.float64]:
        return self.component_weights(deltas).joint()


@dataclass(frozen=True, slots=True)
class SoundSpeedUncertaintyConfig:
    """Stable configuration for a sound-speed uncertainty product.

    ``candidate_radius`` uses degrees with ``planar_degrees`` and kilometres
    with ``great_circle_km``. The former preserves Notebook 6's local-region
    rectangular prefilter; the latter uses a circular great-circle prefilter.
    """

    target_pressure: ArrayLike
    weight_config: WeightConfig
    anchor_time: np.datetime64 | str
    candidate_radius: float
    distance_metric: DistanceMetric = "planar_degrees"
    sensor_support_tau: float = 40.0
    _anchor_time_label: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        pressures = np.asarray(self.target_pressure, dtype=float)
        if pressures.ndim != 1 or pressures.size == 0:
            raise ValueError("target_pressure must be a non-empty one-dimensional array")
        if not np.all(np.isfinite(pressures)):
            raise ValueError("target_pressure must contain only finite values")
        if np.unique(pressures).size != pressures.size:
            raise ValueError("target_pressure values must be unique")
        if not np.isfinite(self.candidate_radius) or self.candidate_radius <= 0:
            raise ValueError("candidate_radius must be a positive finite number")
        if self.distance_metric not in ("planar_degrees", "great_circle_km"):
            raise ValueError("distance_metric must be 'planar_degrees' or 'great_circle_km'")
        if not np.isfinite(self.sensor_support_tau) or self.sensor_support_tau <= 0:
            raise ValueError("sensor_support_tau must be a positive finite number")

        object.__setattr__(self, "target_pressure", tuple(float(value) for value in pressures))
        object.__setattr__(self, "_anchor_time_label", str(self.anchor_time))
        object.__setattr__(self, "anchor_time", np.datetime64(self.anchor_time, "ns"))

    @property
    def anchor_time_label(self) -> str:
        """Return the caller-supplied anchor-time representation for output tables."""

        return self._anchor_time_label

    @classmethod
    def notebook6(cls) -> "SoundSpeedUncertaintyConfig":
        """Return the validated configuration used by the cached Notebook 6 product."""

        seconds_per_year = 365.25 * 24 * 60 * 60
        seconds_per_week = 7 * 24 * 60 * 60
        return cls(
            target_pressure=(5.0, 35.0, 110.0, 500.0),
            weight_config=WeightConfig(
                distance=GaussianScale(1.0 / 3.0),
                time=GaussianScale(3.0 * seconds_per_year),
                season=GaussianScale.from_border(8 * seconds_per_week, 3.0),
                use_distance=True,
                use_time=True,
                use_season=True,
            ),
            anchor_time="2015-07-01",
            candidate_radius=1.0,
            distance_metric="planar_degrees",
            sensor_support_tau=40.0,
        )

    def to_metadata(self) -> dict[str, object]:
        """Return JSON-serializable settings for product provenance."""

        return {
            "target_pressure_dbar": list(self.target_pressure),
            "anchor_time": self.anchor_time_label,
            "candidate_radius": self.candidate_radius,
            "distance_metric": self.distance_metric,
            "sensor_support_tau": self.sensor_support_tau,
            "weighting": {
                "distance_sigma": self.weight_config.distance.sigma,
                "time_sigma_seconds": self.weight_config.time.sigma,
                "season_sigma_seconds": self.weight_config.season.sigma,
                "use_distance": self.weight_config.use_distance,
                "use_time": self.weight_config.use_time,
                "use_season": self.weight_config.use_season,
                "distance_power": self.weight_config.distance_power,
                "time_power": self.weight_config.time_power,
                "season_power": self.weight_config.season_power,
            },
        }


@dataclass(frozen=True, slots=True)
class UncertaintyProductResult:
    """A product table paired with its computational provenance."""

    data: pd.DataFrame
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CandidateQuery:
    """Optional prefilters passed through to :meth:`CycleModels.mask`."""

    lat: tuple[float, float] | None = None
    lon: tuple[float, float] | None = None
    cyclical_dates: tuple[pd.Timestamp, pd.Timestamp] | None = None
    exclude_platform_number: Any = None

    def to_mask_kwargs(self) -> dict[str, object]:
        values: dict[str, object] = {}
        if self.lat is not None:
            values["lat"] = self.lat
        if self.lon is not None:
            values["lon"] = self.lon
        if self.cyclical_dates is not None:
            values["cyclical_dates"] = self.cyclical_dates
        if self.exclude_platform_number is not None:
            values["exclude_platform_number"] = self.exclude_platform_number
        return values


def build_candidate_query(
    *,
    target_latitude: float | None = None,
    target_longitude: float | None = None,
    target_timestamp: pd.Timestamp | None = None,
    dist_rad: float | None = None,
    season_weeks: int | None = None,
    exclude_platform_number: Any = None,
) -> CandidateQuery:
    """Build rectangular spatial and optional wrapped-season candidate filters."""

    using_spatial = any(
        value is not None for value in (target_latitude, target_longitude, dist_rad)
    )
    if using_spatial and None in (target_latitude, target_longitude, dist_rad):
        raise ValueError("target_latitude, target_longitude, and dist_rad are all required")

    using_seasonal = target_timestamp is not None or season_weeks is not None
    if using_seasonal and (target_timestamp is None or season_weeks is None):
        raise ValueError("target_timestamp and season_weeks are both required")

    return CandidateQuery(
        lat=(target_latitude - dist_rad, target_latitude + dist_rad) if using_spatial else None,
        lon=(target_longitude - dist_rad, target_longitude + dist_rad) if using_spatial else None,
        cyclical_dates=(
            target_timestamp - timedelta(weeks=season_weeks),
            target_timestamp + timedelta(weeks=season_weeks),
        )
        if using_seasonal
        else None,
        exclude_platform_number=exclude_platform_number,
    )


def season_fraction(timestamp: np.datetime64 | ArrayLike) -> float | NDArray[np.float64]:
    """Return each timestamp's fraction through its calendar year."""

    timestamp_array = np.atleast_1d(np.asarray(timestamp, dtype="datetime64[ns]"))
    datetime_index = pd.to_datetime(timestamp_array)
    year_period = datetime_index.to_period("Y")
    elapsed = (datetime_index - year_period.start_time) / np.timedelta64(1, "s")
    year_length = ((year_period + 1).start_time - year_period.start_time) / np.timedelta64(1, "s")
    fraction = np.asarray(elapsed / year_length, dtype=float)
    return float(fraction[0]) if np.ndim(timestamp) == 0 else fraction


def seasonal_distance_seconds(
    target_timestamp: np.datetime64, candidate_timestamps: ArrayLike
) -> NDArray[np.float64]:
    """Compute the shortest annual-cycle distance, expressed in seconds."""

    target_fraction = season_fraction(target_timestamp)
    candidate_fraction = season_fraction(candidate_timestamps)
    difference = np.abs(candidate_fraction - target_fraction)
    return np.minimum(difference, 1.0 - difference) * AVERAGE_YEAR_SECONDS


def great_circle_distance_km(
    target_latitude: float,
    target_longitude: float,
    candidate_latitude: ArrayLike,
    candidate_longitude: ArrayLike,
) -> NDArray[np.float64]:
    """Return haversine distances in kilometres with antimeridian wrapping."""

    candidate_latitude_array = np.asarray(candidate_latitude, dtype=float)
    candidate_longitude_array = np.asarray(candidate_longitude, dtype=float)
    latitude_delta = np.deg2rad(candidate_latitude_array - target_latitude)
    longitude_delta = np.deg2rad(
        (candidate_longitude_array - target_longitude + 180.0) % 360.0 - 180.0
    )
    target_latitude_rad = np.deg2rad(target_latitude)
    candidate_latitude_rad = np.deg2rad(candidate_latitude_array)
    haversine = np.square(np.sin(latitude_delta / 2)) + np.cos(target_latitude_rad) * np.cos(
        candidate_latitude_rad
    ) * np.square(np.sin(longitude_delta / 2))
    return 6371.0088 * 2 * np.arcsin(np.sqrt(haversine))


def candidate_mask_for_query(
    candidate_metadata: CycleMetadata,
    *,
    target_latitude: float,
    target_longitude: float,
    candidate_radius: float,
    distance_metric: DistanceMetric,
    exclude_platform_number: Any = None,
) -> NDArray[np.bool_]:
    """Select query candidates under the configured geometry contract."""

    if distance_metric == "planar_degrees":
        mask = (
            (candidate_metadata.latitude >= target_latitude - candidate_radius)
            & (candidate_metadata.latitude <= target_latitude + candidate_radius)
            & (candidate_metadata.longitude >= target_longitude - candidate_radius)
            & (candidate_metadata.longitude <= target_longitude + candidate_radius)
        )
    elif distance_metric == "great_circle_km":
        mask = (
            great_circle_distance_km(
                target_latitude,
                target_longitude,
                candidate_metadata.latitude,
                candidate_metadata.longitude,
            )
            <= candidate_radius
        )
    else:
        raise ValueError("distance_metric must be 'planar_degrees' or 'great_circle_km'")
    if exclude_platform_number is not None:
        mask &= candidate_metadata.platform_number != exclude_platform_number
    return np.asarray(mask, dtype=bool)


def compute_weight_deltas(
    *,
    target_latitude: float,
    target_longitude: float,
    target_timestamp: np.datetime64,
    candidate_metadata: CycleMetadata,
    distance_metric: DistanceMetric = "planar_degrees",
) -> WeightDeltas:
    """Calculate weighting deltas between one query and candidate cycles."""

    if len(candidate_metadata) == 0:
        empty = np.array([], dtype=float)
        return WeightDeltas(distance=empty, time=empty, season=empty)

    if distance_metric == "planar_degrees":
        distance = np.hypot(
            candidate_metadata.latitude - target_latitude,
            candidate_metadata.longitude - target_longitude,
        )
    elif distance_metric == "great_circle_km":
        distance = great_circle_distance_km(
            target_latitude,
            target_longitude,
            candidate_metadata.latitude,
            candidate_metadata.longitude,
        )
    else:
        raise ValueError("distance_metric must be 'planar_degrees' or 'great_circle_km'")
    time = (candidate_metadata.timestamp - target_timestamp) / np.timedelta64(1, "s")
    season = seasonal_distance_seconds(target_timestamp, candidate_metadata.timestamp)
    return WeightDeltas(
        distance=np.asarray(distance, dtype=float),
        time=np.asarray(time, dtype=float),
        season=np.asarray(season, dtype=float),
    )


def weighted_profile_mean(values: ArrayLike, weights: ArrayLike) -> NDArray[np.float64]:
    """Compute a row-wise weighted mean, renormalizing finite support per row."""

    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    if value_array.ndim != 2 or weight_array.ndim != 1 or value_array.shape[1] != weight_array.size:
        raise ValueError("values must be 2-D with one weight per column")
    weight_sum = np.isfinite(value_array) @ weight_array
    weighted_sum = np.nansum(value_array * weight_array, axis=1)
    return np.divide(
        weighted_sum,
        weight_sum,
        out=np.full(value_array.shape[0], np.nan, dtype=float),
        where=weight_sum != 0,
    )


def weighted_profile_variance(variances: ArrayLike, weights: ArrayLike) -> NDArray[np.float64]:
    """Aggregate independent variances with squared normalized weights."""

    variance_array = np.asarray(variances, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    if (
        variance_array.ndim != 2
        or weight_array.ndim != 1
        or variance_array.shape[1] != weight_array.size
    ):
        raise ValueError("variances must be 2-D with one weight per column")
    finite_mask = np.isfinite(variance_array)
    weight_sum = finite_mask @ weight_array
    alpha = np.divide(
        finite_mask * weight_array,
        weight_sum[:, np.newaxis],
        out=np.zeros_like(variance_array, dtype=float),
        where=weight_sum[:, np.newaxis] != 0,
    )
    result = np.nansum(variance_array * np.square(alpha), axis=1)
    result[weight_sum == 0] = np.nan
    return result


def weighted_cycle_prediction(
    interpolates: CycleData, weights: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Predict temperature and salinity from weighted cycle interpolations."""

    return (
        weighted_profile_mean(interpolates.temperature.to_numpy(copy=False), weights),
        weighted_profile_mean(interpolates.salinity.to_numpy(copy=False), weights),
    )


def weighted_component_variance(
    component: ArrayLike, support: ArrayLike, weights: ArrayLike
) -> NDArray[np.float64]:
    """Aggregate a variance component only where its point estimate is finite."""

    component_array = np.asarray(component, dtype=float)
    supported_component = np.where(
        np.isfinite(np.asarray(support, dtype=float)), component_array, np.nan
    )
    return weighted_profile_variance(supported_component, weights)


def effective_cycle_count(values: ArrayLike, weights: ArrayLike) -> NDArray[np.float64]:
    """Return Kish effective sample counts for each target pressure."""

    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    finite_mask = np.isfinite(value_array)
    weight_sum = finite_mask @ weight_array
    squared_weight_sum = finite_mask @ np.square(weight_array)
    return np.divide(
        np.square(weight_sum),
        squared_weight_sum,
        out=np.zeros_like(weight_sum, dtype=float),
        where=squared_weight_sum != 0,
    )


def weighted_support(values: ArrayLike, weights: ArrayLike) -> NDArray[np.float64]:
    """Return raw finite-support mass for each target pressure."""

    return np.isfinite(np.asarray(values, dtype=float)) @ np.asarray(weights, dtype=float)


def estimate_depthwise_spatial_variance(
    cycle_models: CycleModels,
    config: SoundSpeedUncertaintyConfig,
) -> pd.DataFrame:
    """Estimate held-one-platform-out residual variance at each target pressure."""

    pressures = np.asarray(config.target_pressure, dtype=float)
    metadata = cycle_models.metadata()
    rows: list[dict[str, float | str]] = []
    for position, cycle_id in enumerate(metadata.cycle_id):
        candidate_mask = candidate_mask_for_query(
            metadata,
            target_latitude=metadata.latitude[position],
            target_longitude=metadata.longitude[position],
            candidate_radius=config.candidate_radius,
            distance_metric=config.distance_metric,
            exclude_platform_number=metadata.platform_number[position],
        )
        if not candidate_mask.any():
            continue
        candidate_metadata = cycle_models.metadata(candidate_mask)
        weights = config.weight_config.joint_weight(
            compute_weight_deltas(
                target_latitude=metadata.latitude[position],
                target_longitude=metadata.longitude[position],
                target_timestamp=metadata.timestamp[position],
                candidate_metadata=candidate_metadata,
                distance_metric=config.distance_metric,
            )
        )
        predicted_temperature, predicted_salinity = weighted_cycle_prediction(
            cycle_models.interpolate(pressures, mask=candidate_mask), weights
        )
        target = cycle_models[cycle_id].interpolate(pressures)
        for depth_index, pressure in enumerate(pressures):
            values = (
                target.temperature[depth_index],
                target.salinity[depth_index],
                predicted_temperature[depth_index],
                predicted_salinity[depth_index],
            )
            if np.isfinite(values).all():
                rows.append(
                    {
                        "cycle_id": cycle_id,
                        "pressure_dbar": pressure,
                        "temperature_residual": target.temperature[depth_index]
                        - predicted_temperature[depth_index],
                        "salinity_residual": target.salinity[depth_index]
                        - predicted_salinity[depth_index],
                    }
                )

    if not rows:
        return pd.DataFrame(
            index=pd.Index(pressures, name="pressure_dbar"),
            columns=["var_temperature_spatial", "var_salinity_spatial", "spatial_validation_count"],
            dtype=float,
        )
    residuals = pd.DataFrame.from_records(rows)
    result = residuals.groupby("pressure_dbar").agg(
        var_temperature_spatial=("temperature_residual", "var"),
        var_salinity_spatial=("salinity_residual", "var"),
        spatial_validation_count=("cycle_id", "count"),
    )
    return result.reindex(pressures)


class SoundSpeedUncertaintyProduct:
    """Build query-point or gridded TEOS-10 uncertainty product tables.

    ``spatial_variance`` must be indexed by the configured pressure grid and include
    ``var_temperature_spatial``, ``var_salinity_spatial``, and
    ``spatial_validation_count``.  Per-cycle vertical error variance is read
    from the supplied :class:`CycleModels` bundle and combined with this
    separately estimated spatial bucket before TEOS-10 propagation.
    """

    def __init__(
        self,
        cycle_models: CycleModels,
        spatial_variance: pd.DataFrame,
        config: SoundSpeedUncertaintyConfig,
    ) -> None:
        pressures = np.asarray(config.target_pressure, dtype=float)
        missing_columns = set(SPATIAL_VARIANCE_COLUMNS).difference(spatial_variance.columns)
        if missing_columns:
            raise ValueError(f"spatial_variance is missing columns: {sorted(missing_columns)}")
        duplicate_pressures = spatial_variance.index.duplicated()
        if duplicate_pressures.any():
            raise ValueError("spatial_variance index must not contain duplicate pressures")
        missing_pressures = pressures[~np.isin(pressures, spatial_variance.index.to_numpy(float))]
        if missing_pressures.size:
            raise ValueError(
                f"spatial_variance is missing configured pressures: {missing_pressures.tolist()}"
            )
        selected_spatial_variance = spatial_variance.reindex(pressures).copy()
        variance_columns = SPATIAL_VARIANCE_COLUMNS[:2]
        if not np.isfinite(
            selected_spatial_variance.loc[:, variance_columns].to_numpy(float)
        ).all():
            raise ValueError("spatial variance values must be finite")
        if (selected_spatial_variance.loc[:, variance_columns].to_numpy(float) < 0).any():
            raise ValueError("spatial variance values must be non-negative")
        validation_count = selected_spatial_variance["spatial_validation_count"].to_numpy(float)
        if not np.isfinite(validation_count).all() or (validation_count < 0).any():
            raise ValueError("spatial_validation_count must be finite and non-negative")

        self.cycle_models = cycle_models
        self.config = config
        self.target_pressure = pressures
        self.spatial_variance = selected_spatial_variance
        self._cycle_terms: dict[str, NDArray[np.float64]] | None = None

    def _ensure_cycle_terms(self) -> dict[str, NDArray[np.float64]]:
        if self._cycle_terms is not None:
            return self._cycle_terms
        interpolates = self.cycle_models.interpolate(self.target_pressure)
        components = self.cycle_models.interp_error_variance(self.target_pressure)
        self._cycle_terms = {
            "temperature": interpolates.temperature.to_numpy(copy=False),
            "salinity": interpolates.salinity.to_numpy(copy=False),
            "temperature_sensor": components.temperature.sensor_precision.to_numpy(copy=False),
            "temperature_pressure": components.temperature.pressure_gradient.to_numpy(copy=False),
            "temperature_vertical": components.temperature.vertical_model.to_numpy(copy=False),
            "salinity_sensor": components.salinity.sensor_precision.to_numpy(copy=False),
            "salinity_pressure": components.salinity.pressure_gradient.to_numpy(copy=False),
            "salinity_vertical": components.salinity.vertical_model.to_numpy(copy=False),
        }
        return self._cycle_terms

    def precompute_cycle_terms(self) -> None:
        """Cache per-cycle target-pressure estimates and variance components."""

        self._ensure_cycle_terms()

    def metadata(self) -> dict[str, object]:
        """Return JSON-serializable provenance for tables built by this instance."""

        return {
            "schema_version": PRODUCT_SCHEMA_VERSION,
            "configuration": self.config.to_metadata(),
            "cycle_model_count": len(self.cycle_models),
            "spatial_validation_count": self.spatial_variance["spatial_validation_count"].to_dict(),
            "sound_speed_variance_assumptions": {
                "temperature_salinity_covariance": "excluded (independence simplification)",
                "teos10_formula_uncertainty": "excluded",
            },
            "depth_m": "currently mirrors pressure_dbar; physical-depth conversion is future work",
        }

    def _query_data(
        self, latitude: float, longitude: float, *, depth_indices: ArrayLike | None = None
    ) -> pd.DataFrame:
        """Build a product table for one latitude/longitude query point."""

        terms = self._ensure_cycle_terms()
        indices = (
            np.arange(self.target_pressure.size, dtype=int)
            if depth_indices is None
            else np.asarray(depth_indices, dtype=int)
        )
        if indices.ndim != 1 or np.any(indices < 0) or np.any(indices >= self.target_pressure.size):
            raise ValueError("depth_indices must select valid target-pressure indices")

        candidate_mask = candidate_mask_for_query(
            self.cycle_models.metadata(),
            target_latitude=latitude,
            target_longitude=longitude,
            candidate_radius=self.config.candidate_radius,
            distance_metric=self.config.distance_metric,
        )
        if not candidate_mask.any():
            return pd.DataFrame(columns=PRODUCT_COLUMNS)
        weights = self.config.weight_config.joint_weight(
            compute_weight_deltas(
                target_latitude=latitude,
                target_longitude=longitude,
                target_timestamp=self.config.anchor_time,
                candidate_metadata=self.cycle_models.metadata(candidate_mask),
                distance_metric=self.config.distance_metric,
            )
        )
        candidate_indices = np.flatnonzero(candidate_mask)
        temperature_values = terms["temperature"][np.ix_(indices, candidate_indices)]
        salinity_values = terms["salinity"][np.ix_(indices, candidate_indices)]
        temperature = weighted_profile_mean(temperature_values, weights)
        salinity = weighted_profile_mean(salinity_values, weights)

        def component(name: str, support: NDArray[np.float64]) -> NDArray[np.float64]:
            return weighted_component_variance(
                terms[name][np.ix_(indices, candidate_indices)], support, weights
            )

        temp_sensor = component("temperature_sensor", temperature_values)
        temp_pressure = component("temperature_pressure", temperature_values)
        temp_vertical = component("temperature_vertical", temperature_values)
        sal_sensor = component("salinity_sensor", salinity_values)
        sal_pressure = component("salinity_pressure", salinity_values)
        sal_vertical = component("salinity_vertical", salinity_values)
        spatial = self.spatial_variance.iloc[indices]
        temp_spatial = spatial["var_temperature_spatial"].to_numpy(dtype=float)
        sal_spatial = spatial["var_salinity_spatial"].to_numpy(dtype=float)
        temp_aggregate = temp_sensor + temp_pressure + temp_vertical + temp_spatial
        sal_aggregate = sal_sensor + sal_pressure + sal_vertical + sal_spatial
        pressures = self.target_pressure[indices]
        sound_speed = sound_speed_teos10(
            salinity,
            temperature,
            pressures,
            np.full(pressures.size, longitude),
            np.full(pressures.size, latitude),
        )
        partials = sound_speed_teos10_partials(
            salinity,
            temperature,
            pressures,
            np.full(pressures.size, longitude),
            np.full(pressures.size, latitude),
        )
        sound_variance = sound_speed_variance(temp_aggregate, sal_aggregate, partials)
        support_values = np.where(
            np.isfinite(temperature_values), temperature_values, salinity_values
        )
        raw_support = weighted_support(support_values, weights)
        effective_count = effective_cycle_count(support_values, weights)

        result = pd.DataFrame(
            {
                "latitude": latitude,
                "longitude": longitude,
                "depth_m": pressures,
                "pressure_dbar": pressures,
                "timestamp_or_anchor_time": self.config.anchor_time_label,
                "temperature": temperature,
                "salinity": salinity,
                "var_temperature_sensor_precision": temp_sensor,
                "var_temperature_pressure_gradient": temp_pressure,
                "var_temperature_vertical_model": temp_vertical,
                "var_temperature_spatial": temp_spatial,
                "var_temperature_aggregate": temp_aggregate,
                "sigma_temperature_aggregate": np.sqrt(temp_aggregate),
                "var_salinity_sensor_precision": sal_sensor,
                "var_salinity_pressure_gradient": sal_pressure,
                "var_salinity_vertical_model": sal_vertical,
                "var_salinity_spatial": sal_spatial,
                "var_salinity_aggregate": sal_aggregate,
                "sigma_salinity_aggregate": np.sqrt(sal_aggregate),
                "sound_speed_teos10": sound_speed,
                "dc_teos10_dT": partials.temperature,
                "dc_teos10_dS": partials.salinity,
                "var_sound_speed_teos10": sound_variance,
                "sigma_sound_speed_teos10": np.sqrt(sound_variance),
                "W_raw": raw_support,
                "W_display": 1 - np.exp(-raw_support / self.config.sensor_support_tau),
                "candidate_cycle_count": int(candidate_mask.sum()),
                "effective_cycle_count": effective_count,
                "spatial_validation_count": spatial["spatial_validation_count"].to_numpy(),
            }
        )
        temp_factor = np.square(partials.temperature)
        sal_factor = np.square(partials.salinity)
        for source, factor, variance in (
            ("temperature_sensor_precision", temp_factor, temp_sensor),
            ("temperature_pressure_gradient", temp_factor, temp_pressure),
            ("temperature_vertical_model", temp_factor, temp_vertical),
            ("temperature_spatial", temp_factor, temp_spatial),
            ("salinity_sensor_precision", sal_factor, sal_sensor),
            ("salinity_pressure_gradient", sal_factor, sal_pressure),
            ("salinity_vertical_model", sal_factor, sal_vertical),
            ("salinity_spatial", sal_factor, sal_spatial),
        ):
            result[f"var_sound_speed_teos10_from_{source}"] = factor * variance
        result["var_sound_speed_teos10_sensor_bucket"] = (
            result["var_sound_speed_teos10_from_temperature_sensor_precision"]
            + result["var_sound_speed_teos10_from_temperature_pressure_gradient"]
            + result["var_sound_speed_teos10_from_salinity_sensor_precision"]
            + result["var_sound_speed_teos10_from_salinity_pressure_gradient"]
        )
        result["var_sound_speed_teos10_model_bucket"] = (
            result["var_sound_speed_teos10_from_temperature_vertical_model"]
            + result["var_sound_speed_teos10_from_temperature_spatial"]
            + result["var_sound_speed_teos10_from_salinity_vertical_model"]
            + result["var_sound_speed_teos10_from_salinity_spatial"]
        )
        return result.reindex(columns=PRODUCT_COLUMNS)

    def query_result(
        self, latitude: float, longitude: float, *, depth_indices: ArrayLike | None = None
    ) -> UncertaintyProductResult:
        """Build one query table together with the product provenance."""

        data = self._query_data(latitude, longitude, depth_indices=depth_indices)
        metadata = self.metadata()
        data.attrs["argo_interp_uncertainty"] = metadata
        return UncertaintyProductResult(data=data, metadata=metadata)

    def query(
        self, latitude: float, longitude: float, *, depth_indices: ArrayLike | None = None
    ) -> pd.DataFrame:
        """Build a product table for one latitude/longitude query point."""

        return self.query_result(latitude, longitude, depth_indices=depth_indices).data

    def iter_grid_batches(
        self,
        latitudes: Iterable[float],
        longitudes: Iterable[float],
        *,
        depth_indices: ArrayLike | None = None,
        batch_size: int = 256,
    ) -> Iterator[pd.DataFrame]:
        """Yield product tables in bounded query-point batches.

        The yielded frames carry the same metadata in ``DataFrame.attrs`` as
        :meth:`query`. This is the preferred interface for large grids.
        """

        if batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")
        batch: list[pd.DataFrame] = []
        for latitude, longitude in product(latitudes, longitudes):
            frame = self.query(latitude, longitude, depth_indices=depth_indices)
            if not frame.empty:
                batch.append(frame)
            if len(batch) == batch_size:
                yield self._combine_frames(batch)
                batch = []
        if batch:
            yield self._combine_frames(batch)

    def grid_result(
        self,
        latitudes: Iterable[float],
        longitudes: Iterable[float],
        *,
        depth_indices: ArrayLike | None = None,
        batch_size: int = 256,
    ) -> UncertaintyProductResult:
        """Build a full grid table and its provenance.

        For grids too large to hold in memory, consume :meth:`iter_grid_batches`
        instead and persist each yielded frame independently.
        """

        frames = list(
            self.iter_grid_batches(
                latitudes,
                longitudes,
                depth_indices=depth_indices,
                batch_size=batch_size,
            )
        )
        data = self._combine_frames(frames)
        metadata = self.metadata()
        data.attrs["argo_interp_uncertainty"] = metadata
        return UncertaintyProductResult(data=data, metadata=metadata)

    def grid(
        self,
        latitudes: Iterable[float],
        longitudes: Iterable[float],
        *,
        depth_indices: ArrayLike | None = None,
        batch_size: int = 256,
    ) -> pd.DataFrame:
        """Build a complete product table across a Cartesian latitude/longitude grid."""

        return self.grid_result(
            latitudes,
            longitudes,
            depth_indices=depth_indices,
            batch_size=batch_size,
        ).data

    @staticmethod
    def _combine_frames(frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
        nonempty = [frame for frame in frames if not frame.empty]
        return (
            pd.concat(nonempty, ignore_index=True).reindex(columns=PRODUCT_COLUMNS)
            if nonempty
            else pd.DataFrame(columns=PRODUCT_COLUMNS)
        )


def depth_summary(product: pd.DataFrame) -> pd.DataFrame:
    """Summarize the standard Notebook 6 product diagnostics by target depth."""

    required = {
        "depth_m",
        "sigma_sound_speed_teos10",
        "W_raw",
        "W_display",
        "effective_cycle_count",
        "candidate_cycle_count",
    }
    missing = required.difference(product.columns)
    if missing:
        raise ValueError(f"product is missing columns: {sorted(missing)}")
    return product.groupby("depth_m", as_index=False).agg(
        row_count=("sigma_sound_speed_teos10", "size"),
        finite_sigma_count=("sigma_sound_speed_teos10", lambda values: int(values.notna().sum())),
        sigma_sound_speed_teos10_p01=(
            "sigma_sound_speed_teos10",
            lambda values: values.quantile(0.01),
        ),
        sigma_sound_speed_teos10_median=("sigma_sound_speed_teos10", "median"),
        sigma_sound_speed_teos10_p99=(
            "sigma_sound_speed_teos10",
            lambda values: values.quantile(0.99),
        ),
        W_raw_median=("W_raw", "median"),
        W_display_median=("W_display", "median"),
        effective_cycle_count_median=("effective_cycle_count", "median"),
        candidate_cycle_count_median=("candidate_cycle_count", "median"),
    )


__all__ = [
    "AVERAGE_YEAR_SECONDS",
    "CandidateQuery",
    "DistanceMetric",
    "GaussianScale",
    "PRODUCT_COLUMNS",
    "PRODUCT_SCHEMA_VERSION",
    "SPATIAL_VARIANCE_COLUMNS",
    "SoundSpeedUncertaintyConfig",
    "SoundSpeedUncertaintyProduct",
    "UncertaintyProductResult",
    "WeightComponents",
    "WeightConfig",
    "WeightDeltas",
    "build_candidate_query",
    "candidate_mask_for_query",
    "compute_weight_deltas",
    "depth_summary",
    "effective_cycle_count",
    "estimate_depthwise_spatial_variance",
    "great_circle_distance_km",
    "season_fraction",
    "seasonal_distance_seconds",
    "weighted_component_variance",
    "weighted_cycle_prediction",
    "weighted_profile_mean",
    "weighted_profile_variance",
    "weighted_support",
]
