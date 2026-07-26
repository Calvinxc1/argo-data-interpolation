from __future__ import annotations

import json
import pickle
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import gsw
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

notebook_dir = Path(__file__).resolve().parent
repo_root = notebook_dir.parents[2]
if str(notebook_dir) not in sys.path:
    sys.path.insert(0, str(notebook_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from argo_interp.acoustics import (  # noqa: E402
    sound_speed_teos10,
    sound_speed_teos10_partials,
    sound_speed_variance,
)
from lib import (  # noqa: E402
    GaussianScale,
    WeightConfig,
    WeightDeltas,
    seasonal_distance_seconds,
    weighted_profile_mean,
    weighted_profile_variance,
)


data_path = notebook_dir / "data"
cycle_model_cache_path = data_path / "pchip_cycle_models.pkl"
metadata_path = data_path / "sound_speed_uncertainty_product_metadata.json"

detail_path = data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_detail.csv"
cycle_summary_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_cycle_summary.csv"
)
predictor_summary_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_predictor_summary.csv"
)
depth_summary_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_depth_summary.csv"
)
coverage_summary_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_sigma_coverage.csv"
)
spatial_variance_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_spatial_variance.csv"
)
run_metadata_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_metadata.json"
)
terms_cache_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_terms.pkl"
)
terms_metadata_path = (
    data_path / "sound_speed_uncertainty_holdout_validation_replication_grid_terms_metadata.json"
)

depth_grid_m = np.arange(5.0, 501.0, 1.0)
min_cycles = 30
detail_chunk_size = 100_000
predictors = ("notebook6", "flat_jana")
variables = ("temperature", "salinity", "sound_speed_teos10")
sigma_variants = ("no_spatial", "with_spatial")


def metadata_matches(path: Path, expected: dict[str, object]) -> bool:
    if not path.exists():
        return False
    with path.open() as f:
        observed = json.load(f)
    return observed == expected


def build_weight_config(product_metadata: dict[str, object]) -> WeightConfig:
    seconds_per_year = 365.25 * 24 * 60 * 60
    seconds_per_week = 7 * 24 * 60 * 60
    return WeightConfig(
        distance=GaussianScale(float(product_metadata["distance_kernel_sigma_deg"])),
        time=GaussianScale(float(product_metadata["year_stdev"]) * seconds_per_year),
        season=GaussianScale.from_border(
            float(product_metadata["season_weeks"]) * seconds_per_week,
            float(product_metadata["season_week_stdev"]),
        ),
        use_distance=bool(product_metadata["use_distance_weight"]),
        use_time=bool(product_metadata["use_time_weight"]),
        use_season=bool(product_metadata["use_season_weight"]),
    )


def effective_cycle_count(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    finite_mask = np.isfinite(values)
    weight_sum = finite_mask @ weights
    squared_weight_sum = finite_mask @ np.square(weights)
    return np.divide(
        np.square(weight_sum),
        squared_weight_sum,
        out=np.zeros_like(weight_sum, dtype=float),
        where=squared_weight_sum != 0,
    )


def weighted_support(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return np.isfinite(values) @ weights


def weighted_component_variance(
    component: np.ndarray,
    support: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    supported_component = np.where(np.isfinite(support), component, np.nan)
    return weighted_profile_variance(supported_component, weights)


def rmse(errors: np.ndarray) -> float:
    finite = errors[np.isfinite(errors)]
    if finite.size == 0:
        return np.nan
    return float(np.sqrt(np.mean(np.square(finite))))


def mae(errors: np.ndarray) -> float:
    finite = errors[np.isfinite(errors)]
    if finite.size == 0:
        return np.nan
    return float(np.mean(np.abs(finite)))


@dataclass(slots=True)
class ReplicationGridTerms:
    pressure_by_cycle: np.ndarray
    temperature_by_cycle: np.ndarray
    salinity_by_cycle: np.ndarray
    temperature_sensor_variance_by_cycle: np.ndarray
    temperature_pressure_variance_by_cycle: np.ndarray
    temperature_vertical_variance_by_cycle: np.ndarray
    salinity_sensor_variance_by_cycle: np.ndarray
    salinity_pressure_variance_by_cycle: np.ndarray
    salinity_vertical_variance_by_cycle: np.ndarray


class OnlineDepthVariance:
    def __init__(self, n_depths: int) -> None:
        self.count = np.zeros(n_depths, dtype=np.int64)
        self.mean = np.zeros(n_depths, dtype=float)
        self.m2 = np.zeros(n_depths, dtype=float)

    def update(self, values: np.ndarray) -> None:
        finite = np.isfinite(values)
        if not np.any(finite):
            return
        delta = values[finite] - self.mean[finite]
        self.count[finite] += 1
        self.mean[finite] += delta / self.count[finite]
        delta2 = values[finite] - self.mean[finite]
        self.m2[finite] += delta * delta2

    def variance(self) -> np.ndarray:
        return np.divide(
            self.m2,
            self.count - 1,
            out=np.full_like(self.m2, np.nan, dtype=float),
            where=self.count > 1,
        )


class DepthErrorStats:
    def __init__(self, n_depths: int) -> None:
        self.count = np.zeros(n_depths, dtype=np.int64)
        self.sum = np.zeros(n_depths, dtype=float)
        self.sum_abs = np.zeros(n_depths, dtype=float)
        self.sum_sq = np.zeros(n_depths, dtype=float)

    def update(self, errors: np.ndarray) -> None:
        finite = np.isfinite(errors)
        values = errors[finite]
        self.count[finite] += 1
        self.sum[finite] += values
        self.sum_abs[finite] += np.abs(values)
        self.sum_sq[finite] += np.square(values)

    def to_rows(self, predictor: str, variable: str) -> list[dict[str, object]]:
        rows = []
        for index, depth in enumerate(depth_grid_m):
            count = int(self.count[index])
            rows.append(
                {
                    "predictor": predictor,
                    "variable": variable,
                    "depth_m": depth,
                    "count": count,
                    "bias": self.sum[index] / count if count else np.nan,
                    "mae": self.sum_abs[index] / count if count else np.nan,
                    "rmse": np.sqrt(self.sum_sq[index] / count) if count else np.nan,
                }
            )
        return rows


class CoverageStats:
    def __init__(self, n_depths: int) -> None:
        self.count = np.zeros(n_depths, dtype=np.int64)
        self.within_1sigma = np.zeros(n_depths, dtype=np.int64)
        self.within_2sigma = np.zeros(n_depths, dtype=np.int64)

    def update(self, errors: np.ndarray, sigma: np.ndarray) -> None:
        finite = np.isfinite(errors) & np.isfinite(sigma)
        abs_error = np.abs(errors[finite])
        sigma_values = sigma[finite]
        self.count[finite] += 1
        self.within_1sigma[finite] += abs_error <= sigma_values
        self.within_2sigma[finite] += abs_error <= 2 * sigma_values

    def to_rows(self, predictor: str, variable: str, sigma_variant: str) -> list[dict[str, object]]:
        rows = []
        pooled_count = int(self.count.sum())
        pooled_1 = int(self.within_1sigma.sum())
        pooled_2 = int(self.within_2sigma.sum())
        rows.append(
            {
                "scope": "pooled",
                "predictor": predictor,
                "variable": variable,
                "sigma_variant": sigma_variant,
                "depth_m": np.nan,
                "count": pooled_count,
                "within_1sigma_fraction": pooled_1 / pooled_count if pooled_count else np.nan,
                "within_2sigma_fraction": pooled_2 / pooled_count if pooled_count else np.nan,
                "normal_expected_1sigma": 0.683,
                "normal_expected_2sigma": 0.954,
            }
        )
        for index, depth in enumerate(depth_grid_m):
            count = int(self.count[index])
            rows.append(
                {
                    "scope": "depth",
                    "predictor": predictor,
                    "variable": variable,
                    "sigma_variant": sigma_variant,
                    "depth_m": depth,
                    "count": count,
                    "within_1sigma_fraction": (
                        self.within_1sigma[index] / count if count else np.nan
                    ),
                    "within_2sigma_fraction": (
                        self.within_2sigma[index] / count if count else np.nan
                    ),
                    "normal_expected_1sigma": 0.683,
                    "normal_expected_2sigma": 0.954,
                }
            )
        return rows


def build_replication_grid_terms(cycle_models, metadata) -> ReplicationGridTerms:
    n_depths = len(depth_grid_m)
    n_cycles = len(metadata)
    pressure_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    temperature_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    salinity_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    temperature_sensor_variance_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    temperature_pressure_variance_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    temperature_vertical_variance_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    salinity_sensor_variance_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    salinity_pressure_variance_by_cycle = np.empty((n_depths, n_cycles), dtype=float)
    salinity_vertical_variance_by_cycle = np.empty((n_depths, n_cycles), dtype=float)

    for position, cycle_id in enumerate(tqdm(metadata.cycle_id, desc="meter-grid terms")):
        pressure = np.asarray(gsw.p_from_z(-depth_grid_m, metadata.latitude[position]), dtype=float)
        interpolated = cycle_models[cycle_id].interpolate(pressure)
        variance = cycle_models[cycle_id].interp_error_variance(pressure)

        pressure_by_cycle[:, position] = pressure
        temperature_by_cycle[:, position] = interpolated.temperature
        salinity_by_cycle[:, position] = interpolated.salinity
        temperature_sensor_variance_by_cycle[:, position] = variance.temperature.sensor_precision
        temperature_pressure_variance_by_cycle[:, position] = variance.temperature.pressure_gradient
        temperature_vertical_variance_by_cycle[:, position] = variance.temperature.vertical_model
        salinity_sensor_variance_by_cycle[:, position] = variance.salinity.sensor_precision
        salinity_pressure_variance_by_cycle[:, position] = variance.salinity.pressure_gradient
        salinity_vertical_variance_by_cycle[:, position] = variance.salinity.vertical_model

    return ReplicationGridTerms(
        pressure_by_cycle=pressure_by_cycle,
        temperature_by_cycle=temperature_by_cycle,
        salinity_by_cycle=salinity_by_cycle,
        temperature_sensor_variance_by_cycle=temperature_sensor_variance_by_cycle,
        temperature_pressure_variance_by_cycle=temperature_pressure_variance_by_cycle,
        temperature_vertical_variance_by_cycle=temperature_vertical_variance_by_cycle,
        salinity_sensor_variance_by_cycle=salinity_sensor_variance_by_cycle,
        salinity_pressure_variance_by_cycle=salinity_pressure_variance_by_cycle,
        salinity_vertical_variance_by_cycle=salinity_vertical_variance_by_cycle,
    )


def load_or_build_replication_grid_terms(cycle_models, metadata) -> ReplicationGridTerms:
    expected_metadata = {
        "cycle_model_cache": str(cycle_model_cache_path),
        "cycle_model_cache_mtime_ns": cycle_model_cache_path.stat().st_mtime_ns,
        "cycle_count": int(len(metadata)),
        "depth_grid_m_start": float(depth_grid_m[0]),
        "depth_grid_m_stop": float(depth_grid_m[-1]),
        "depth_grid_m_step": 1.0,
        "depth_grid_m_count": int(len(depth_grid_m)),
        "pressure_conversion": "gsw.p_from_z(-depth_m, cycle_latitude), per cycle",
    }
    if terms_cache_path.exists() and metadata_matches(terms_metadata_path, expected_metadata):
        with terms_cache_path.open("rb") as f:
            return pickle.load(f)

    terms = build_replication_grid_terms(cycle_models, metadata)
    with terms_cache_path.open("wb") as f:
        pickle.dump(terms, f)
    with terms_metadata_path.open("w") as f:
        json.dump(expected_metadata, f, indent=2, sort_keys=True)
        f.write("\n")
    return terms


def candidate_indices_for_target(
    position: int,
    *,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    platform_numbers: np.ndarray,
    dist_rad: float,
) -> np.ndarray:
    return np.flatnonzero(
        (np.abs(latitudes - latitudes[position]) <= dist_rad)
        & (np.abs(longitudes - longitudes[position]) <= dist_rad)
        & (platform_numbers != platform_numbers[position])
    )


def notebook6_weights_for_target(
    position: int,
    candidate_indices: np.ndarray,
    *,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    timestamps: np.ndarray,
    weight_config: WeightConfig,
) -> np.ndarray:
    deltas = WeightDeltas(
        distance=np.sqrt(
            np.square(latitudes[candidate_indices] - latitudes[position])
            + np.square(longitudes[candidate_indices] - longitudes[position])
        ),
        time=(timestamps[candidate_indices] - timestamps[position]) / np.timedelta64(1, "s"),
        season=seasonal_distance_seconds(
            target_timestamp=timestamps[position],
            candidate_timestamps=timestamps[candidate_indices],
        ),
    )
    return weight_config.joint_weight(deltas)


def predictor_arrays(
    candidate_indices: np.ndarray,
    weights: np.ndarray,
    terms: ReplicationGridTerms,
) -> dict[str, np.ndarray]:
    candidate_temperature = terms.temperature_by_cycle[:, candidate_indices]
    candidate_salinity = terms.salinity_by_cycle[:, candidate_indices]
    support_values = np.where(np.isfinite(candidate_temperature), candidate_temperature, candidate_salinity)

    predicted_temperature = weighted_profile_mean(candidate_temperature, weights)
    predicted_salinity = weighted_profile_mean(candidate_salinity, weights)

    var_temperature_sensor = weighted_component_variance(
        terms.temperature_sensor_variance_by_cycle[:, candidate_indices],
        candidate_temperature,
        weights,
    )
    var_temperature_pressure = weighted_component_variance(
        terms.temperature_pressure_variance_by_cycle[:, candidate_indices],
        candidate_temperature,
        weights,
    )
    var_temperature_vertical = weighted_component_variance(
        terms.temperature_vertical_variance_by_cycle[:, candidate_indices],
        candidate_temperature,
        weights,
    )
    var_salinity_sensor = weighted_component_variance(
        terms.salinity_sensor_variance_by_cycle[:, candidate_indices],
        candidate_salinity,
        weights,
    )
    var_salinity_pressure = weighted_component_variance(
        terms.salinity_pressure_variance_by_cycle[:, candidate_indices],
        candidate_salinity,
        weights,
    )
    var_salinity_vertical = weighted_component_variance(
        terms.salinity_vertical_variance_by_cycle[:, candidate_indices],
        candidate_salinity,
        weights,
    )

    return {
        "predicted_temperature": predicted_temperature,
        "predicted_salinity": predicted_salinity,
        "var_temperature_no_spatial": (
            var_temperature_sensor + var_temperature_pressure + var_temperature_vertical
        ),
        "var_salinity_no_spatial": var_salinity_sensor + var_salinity_pressure + var_salinity_vertical,
        "weighted_support": weighted_support(support_values, weights),
        "effective_cycle_count": effective_cycle_count(support_values, weights),
        "weight_sum": np.full(len(depth_grid_m), float(np.sum(weights))),
    }


def estimate_notebook6_spatial_variance(
    metadata,
    terms: ReplicationGridTerms,
    weight_config: WeightConfig,
    dist_rad: float,
) -> tuple[pd.DataFrame, dict[str, int]]:
    latitudes = metadata.latitude
    longitudes = metadata.longitude
    timestamps = metadata.timestamp
    platform_numbers = metadata.platform_number
    temperature_residuals = OnlineDepthVariance(len(depth_grid_m))
    salinity_residuals = OnlineDepthVariance(len(depth_grid_m))
    skipped_low_support = 0

    for position in tqdm(range(len(metadata)), desc="notebook6 spatial variance"):
        candidate_indices = candidate_indices_for_target(
            position,
            latitudes=latitudes,
            longitudes=longitudes,
            platform_numbers=platform_numbers,
            dist_rad=dist_rad,
        )
        if len(candidate_indices) < min_cycles:
            skipped_low_support += 1
            continue

        weights = notebook6_weights_for_target(
            position,
            candidate_indices,
            latitudes=latitudes,
            longitudes=longitudes,
            timestamps=timestamps,
            weight_config=weight_config,
        )
        predicted_temperature = weighted_profile_mean(
            terms.temperature_by_cycle[:, candidate_indices],
            weights,
        )
        predicted_salinity = weighted_profile_mean(
            terms.salinity_by_cycle[:, candidate_indices],
            weights,
        )
        temperature_residuals.update(terms.temperature_by_cycle[:, position] - predicted_temperature)
        salinity_residuals.update(terms.salinity_by_cycle[:, position] - predicted_salinity)

    spatial_variance = pd.DataFrame(
        {
            "depth_m": depth_grid_m,
            "var_temperature_spatial": temperature_residuals.variance(),
            "var_salinity_spatial": salinity_residuals.variance(),
            "spatial_validation_count_temperature": temperature_residuals.count,
            "spatial_validation_count_salinity": salinity_residuals.count,
        }
    )
    return spatial_variance, {"skipped_cycle_count_low_support": skipped_low_support}


def append_detail_rows(rows: list[dict[str, object]], *, write_header: bool) -> None:
    if not rows:
        return
    pd.DataFrame.from_records(rows).to_csv(
        detail_path,
        mode="w" if write_header else "a",
        index=False,
        header=write_header,
    )
    rows.clear()


def predictor_cycle_summary(
    *,
    predictor: str,
    cycle_id: str,
    metadata,
    position: int,
    candidate_count: int,
    errors: dict[str, np.ndarray],
) -> dict[str, object]:
    row: dict[str, object] = {
        "predictor": predictor,
        "cycle_id": cycle_id,
        "platform_number": metadata.platform_number[position],
        "cycle_number": metadata.cycle_number[position],
        "direction": metadata.direction[position],
        "latitude": float(metadata.latitude[position]),
        "longitude": float(metadata.longitude[position]),
        "timestamp": str(pd.Timestamp(metadata.timestamp[position])),
        "candidate_count": candidate_count,
    }
    for variable, values in errors.items():
        row[f"{variable}_level_count"] = int(np.isfinite(values).sum())
        row[f"{variable}_rmse"] = rmse(values)
        row[f"{variable}_mae"] = mae(values)
        row[f"{variable}_bias"] = (
            float(np.nanmean(values)) if np.any(np.isfinite(values)) else np.nan
        )
    return row


def summarize_predictors(cycle_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for predictor in predictors:
        predictor_cycles = cycle_summary[cycle_summary["predictor"] == predictor]
        for variable in variables:
            for metric in ("rmse", "mae", "bias"):
                values = predictor_cycles[f"{variable}_{metric}"].dropna()
                rows.append(
                    {
                        "predictor": predictor,
                        "variable": variable,
                        "metric": metric,
                        "cycle_count": int(values.size),
                        "mean": float(values.mean()) if not values.empty else np.nan,
                        "p25": float(values.quantile(0.25)) if not values.empty else np.nan,
                        "median": float(values.median()) if not values.empty else np.nan,
                        "p75": float(values.quantile(0.75)) if not values.empty else np.nan,
                        "p90": float(values.quantile(0.90)) if not values.empty else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def print_headline(predictor_summary: pd.DataFrame) -> None:
    for variable in variables:
        metric_rows = predictor_summary[
            (predictor_summary["variable"] == variable)
            & (predictor_summary["metric"] == "rmse")
        ].set_index("predictor")
        if set(predictors).issubset(metric_rows.index):
            notebook6_p75 = metric_rows.loc["notebook6", "p75"]
            flat_p75 = metric_rows.loc["flat_jana", "p75"]
            delta = notebook6_p75 - flat_p75
            pct = 100 * delta / flat_p75 if flat_p75 else np.nan
            winner = "notebook6" if delta < 0 else "flat_jana"
            print(
                f"{variable} p75 per-cycle RMSE: notebook6={notebook6_p75:.6g}, "
                f"flat_jana={flat_p75:.6g}, delta={delta:.6g} ({pct:.2f}%), "
                f"winner={winner}"
            )


def run_validation(
    metadata,
    terms: ReplicationGridTerms,
    spatial_variance: pd.DataFrame,
    weight_config: WeightConfig,
    dist_rad: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if detail_path.exists():
        detail_path.unlink()

    latitudes = metadata.latitude
    longitudes = metadata.longitude
    timestamps = metadata.timestamp
    platform_numbers = metadata.platform_number
    var_temperature_spatial = spatial_variance["var_temperature_spatial"].to_numpy(dtype=float)
    var_salinity_spatial = spatial_variance["var_salinity_spatial"].to_numpy(dtype=float)

    depth_stats = {
        (predictor, variable): DepthErrorStats(len(depth_grid_m))
        for predictor in predictors
        for variable in variables
    }
    coverage_stats = {
        (predictor, variable, sigma_variant): CoverageStats(len(depth_grid_m))
        for predictor in predictors
        for variable in variables
        for sigma_variant in sigma_variants
    }

    cycle_rows = []
    detail_rows: list[dict[str, object]] = []
    skipped_low_support = 0
    write_header = True

    for position, cycle_id in enumerate(tqdm(metadata.cycle_id, desc="matched holdout")):
        candidate_indices = candidate_indices_for_target(
            position,
            latitudes=latitudes,
            longitudes=longitudes,
            platform_numbers=platform_numbers,
            dist_rad=dist_rad,
        )
        candidate_count = int(len(candidate_indices))
        if candidate_count < min_cycles:
            skipped_low_support += 1
            continue

        notebook6_weights = notebook6_weights_for_target(
            position,
            candidate_indices,
            latitudes=latitudes,
            longitudes=longitudes,
            timestamps=timestamps,
            weight_config=weight_config,
        )
        flat_weights = np.ones(candidate_count, dtype=float)

        target_pressure = terms.pressure_by_cycle[:, position]
        target_temperature = terms.temperature_by_cycle[:, position]
        target_salinity = terms.salinity_by_cycle[:, position]
        lon_array = np.full_like(depth_grid_m, float(longitudes[position]), dtype=float)
        lat_array = np.full_like(depth_grid_m, float(latitudes[position]), dtype=float)
        target_sound_speed = sound_speed_teos10(
            target_salinity,
            target_temperature,
            target_pressure,
            lon_array,
            lat_array,
        )

        predictor_outputs = {
            "notebook6": predictor_arrays(candidate_indices, notebook6_weights, terms),
            "flat_jana": predictor_arrays(candidate_indices, flat_weights, terms),
        }

        cycle_error_payload: dict[str, dict[str, np.ndarray]] = {}
        per_depth_payload: dict[str, dict[str, np.ndarray]] = {}
        for predictor, output in predictor_outputs.items():
            predicted_sound_speed = sound_speed_teos10(
                output["predicted_salinity"],
                output["predicted_temperature"],
                target_pressure,
                lon_array,
                lat_array,
            )
            partials = sound_speed_teos10_partials(
                output["predicted_salinity"],
                output["predicted_temperature"],
                target_pressure,
                lon_array,
                lat_array,
            )

            var_temperature_no_spatial = output["var_temperature_no_spatial"]
            var_salinity_no_spatial = output["var_salinity_no_spatial"]
            var_temperature_with_spatial = var_temperature_no_spatial + var_temperature_spatial
            var_salinity_with_spatial = var_salinity_no_spatial + var_salinity_spatial
            var_sound_no_spatial = sound_speed_variance(
                var_temperature_no_spatial,
                var_salinity_no_spatial,
                partials,
            )
            var_sound_with_spatial = sound_speed_variance(
                var_temperature_with_spatial,
                var_salinity_with_spatial,
                partials,
            )

            errors = {
                "temperature": output["predicted_temperature"] - target_temperature,
                "salinity": output["predicted_salinity"] - target_salinity,
                "sound_speed_teos10": predicted_sound_speed - target_sound_speed,
            }
            sigmas = {
                ("temperature", "no_spatial"): np.sqrt(var_temperature_no_spatial),
                ("temperature", "with_spatial"): np.sqrt(var_temperature_with_spatial),
                ("salinity", "no_spatial"): np.sqrt(var_salinity_no_spatial),
                ("salinity", "with_spatial"): np.sqrt(var_salinity_with_spatial),
                ("sound_speed_teos10", "no_spatial"): np.sqrt(var_sound_no_spatial),
                ("sound_speed_teos10", "with_spatial"): np.sqrt(var_sound_with_spatial),
            }

            for variable, error in errors.items():
                depth_stats[(predictor, variable)].update(error)
                for sigma_variant in sigma_variants:
                    coverage_stats[(predictor, variable, sigma_variant)].update(
                        error,
                        sigmas[(variable, sigma_variant)],
                    )

            cycle_rows.append(
                predictor_cycle_summary(
                    predictor=predictor,
                    cycle_id=cycle_id,
                    metadata=metadata,
                    position=position,
                    candidate_count=candidate_count,
                    errors=errors,
                )
            )
            cycle_error_payload[predictor] = errors
            per_depth_payload[predictor] = {
                "predicted_temperature": output["predicted_temperature"],
                "predicted_salinity": output["predicted_salinity"],
                "predicted_sound_speed_teos10": predicted_sound_speed,
                "temperature_error": errors["temperature"],
                "salinity_error": errors["salinity"],
                "sound_speed_teos10_error": errors["sound_speed_teos10"],
                "sigma_temperature_no_spatial": sigmas[("temperature", "no_spatial")],
                "sigma_temperature_with_spatial": sigmas[("temperature", "with_spatial")],
                "sigma_salinity_no_spatial": sigmas[("salinity", "no_spatial")],
                "sigma_salinity_with_spatial": sigmas[("salinity", "with_spatial")],
                "sigma_sound_speed_teos10_no_spatial": sigmas[
                    ("sound_speed_teos10", "no_spatial")
                ],
                "sigma_sound_speed_teos10_with_spatial": sigmas[
                    ("sound_speed_teos10", "with_spatial")
                ],
                "weighted_support": output["weighted_support"],
                "effective_cycle_count": output["effective_cycle_count"],
                "weight_sum": output["weight_sum"],
            }

        for depth_index, depth in enumerate(depth_grid_m):
            row: dict[str, object] = {
                "cycle_id": cycle_id,
                "platform_number": platform_numbers[position],
                "cycle_number": metadata.cycle_number[position],
                "direction": metadata.direction[position],
                "latitude": float(latitudes[position]),
                "longitude": float(longitudes[position]),
                "timestamp": str(pd.Timestamp(timestamps[position])),
                "depth_m": depth,
                "pressure_dbar": target_pressure[depth_index],
                "target_temperature": target_temperature[depth_index],
                "target_salinity": target_salinity[depth_index],
                "target_sound_speed_teos10": target_sound_speed[depth_index],
                "candidate_count": candidate_count,
            }
            for predictor in predictors:
                for field, values in per_depth_payload[predictor].items():
                    row[f"{predictor}_{field}"] = values[depth_index]
            detail_rows.append(row)

        if len(detail_rows) >= detail_chunk_size:
            append_detail_rows(detail_rows, write_header=write_header)
            write_header = False

    append_detail_rows(detail_rows, write_header=write_header)

    cycle_summary = pd.DataFrame.from_records(cycle_rows)
    predictor_summary = summarize_predictors(cycle_summary)

    depth_rows = []
    for (predictor, variable), stats in depth_stats.items():
        depth_rows.extend(stats.to_rows(predictor, variable))
    depth_summary = pd.DataFrame.from_records(depth_rows)

    coverage_rows = []
    for (predictor, variable, sigma_variant), stats in coverage_stats.items():
        coverage_rows.extend(stats.to_rows(predictor, variable, sigma_variant))
    coverage_summary = pd.DataFrame.from_records(coverage_rows)

    cycle_summary.to_csv(cycle_summary_path, index=False)
    predictor_summary.to_csv(predictor_summary_path, index=False)
    depth_summary.to_csv(depth_summary_path, index=False)
    coverage_summary.to_csv(coverage_summary_path, index=False)

    print(f"skipped_cycle_count_low_support={skipped_low_support}")
    return cycle_summary, predictor_summary, depth_summary


def main() -> None:
    start = time.perf_counter()

    with metadata_path.open() as f:
        product_metadata = json.load(f)

    weight_config = build_weight_config(product_metadata)
    dist_rad = float(product_metadata["dist_rad"])

    with cycle_model_cache_path.open("rb") as f:
        cycle_model_bundle = pickle.load(f)
    cycle_models = cycle_model_bundle["cycle_models"]
    metadata = cycle_models.metadata()

    terms = load_or_build_replication_grid_terms(cycle_models, metadata)

    spatial_variance, spatial_variance_diagnostics = estimate_notebook6_spatial_variance(
        metadata,
        terms,
        weight_config,
        dist_rad,
    )
    spatial_variance.to_csv(spatial_variance_path, index=False)

    cycle_summary, predictor_summary, depth_summary = run_validation(
        metadata,
        terms,
        spatial_variance,
        weight_config,
        dist_rad,
    )

    elapsed_seconds = time.perf_counter() - start
    run_metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "cycle_model_cache": str(cycle_model_cache_path),
        "product_metadata": product_metadata,
        "validation_design": {
            "name": "matched_replication_grid_hold_one_float_out",
            "depth_grid_m": depth_grid_m.tolist(),
            "depth_grid_m_count": int(len(depth_grid_m)),
            "depth_grid_m_summary": "5 to 500 m inclusive, 1 m spacing",
            "pressure_conversion": (
                "The replication grid is in meters. For each cycle, the script converts "
                "depth_m to pressure_dbar with gsw.p_from_z(-depth_m, cycle_latitude), "
                "then interpolates that cycle's PCHIP model at those pressures."
            ),
            "withholding": (
                "Hold-one-float-out: all cycles from the held-out platform are excluded "
                "from the candidate set for both predictors."
            ),
            "cycle_set": (
                "Both predictors are evaluated on the same held-out cycles. Cycles with "
                f"fewer than {min_cycles} candidate cycles in the shared 2 degree by 2 "
                "degree spatial window are skipped for both predictors."
            ),
            "aggregation": (
                "For each held-out cycle and predictor, RMSE, MAE, and bias are computed "
                "across finite levels for each variable. Predictor summaries report mean, "
                "p25, median, p75, p90, and cycle count across held-out cycles. Depth "
                "summaries report pooled count, bias, MAE, and RMSE at each depth."
            ),
            "predictors": {
                "notebook6": (
                    "Final notebook 6 distance * absolute-time * wrapped-season Gaussian "
                    "weights inside the shared 1 degree half-width spatial prefilter."
                ),
                "flat_jana": (
                    "Flat Jana-style 2 degree by 2 degree box, equal candidate weights, "
                    f"min_cycles={min_cycles}."
                ),
            },
            "variables": list(variables),
            "sound_speed_equation": "TEOS-10 via gsw",
            "nan_rule": (
                "Per-cycle RMSE/MAE use only finite depth-level errors for that cycle, "
                "predictor, and variable. Depth and coverage summaries likewise count "
                "only finite error/sigma pairs. Level counts are reported in the cycle "
                "summary and each detail row remains present even when one variable is NaN."
            ),
            "sigma_variants": {
                "no_spatial": (
                    "Weighted propagated sensor precision, pressure-gradient, and vertical "
                    "model variances only."
                ),
                "with_spatial": (
                    "The no_spatial variance plus a depthwise spatial variance bucket "
                    "estimated from the notebook6 matched hold-one-float-out residuals "
                    "on this same 5-500 m grid."
                ),
            },
        },
        "cycle_count": int(len(metadata)),
        "evaluated_cycle_count": int(cycle_summary["cycle_id"].nunique()),
        "detail_row_count": int(len(depth_grid_m) * cycle_summary["cycle_id"].nunique()),
        "spatial_variance_diagnostics": spatial_variance_diagnostics,
        "detail_csv": str(detail_path),
        "cycle_summary_csv": str(cycle_summary_path),
        "predictor_summary_csv": str(predictor_summary_path),
        "depth_summary_csv": str(depth_summary_path),
        "coverage_summary_csv": str(coverage_summary_path),
        "spatial_variance_csv": str(spatial_variance_path),
    }
    with run_metadata_path.open("w") as f:
        json.dump(run_metadata, f, indent=2, sort_keys=True)
        f.write("\n")

    print(predictor_summary.to_string(index=False))
    print_headline(predictor_summary)
    print(f"\nwrote {detail_path}")
    print(f"wrote {cycle_summary_path}")
    print(f"wrote {predictor_summary_path}")
    print(f"wrote {depth_summary_path}")
    print(f"wrote {coverage_summary_path}")
    print(f"wrote {spatial_variance_path}")
    print(f"wrote {run_metadata_path}")
    print(f"elapsed_seconds={elapsed_seconds:.2f}")


if __name__ == "__main__":
    main()
