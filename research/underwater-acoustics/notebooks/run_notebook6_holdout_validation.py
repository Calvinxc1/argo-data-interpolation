from __future__ import annotations

import json
import pickle
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

notebook_dir = Path(__file__).resolve().parent
repo_root = notebook_dir.parents[2]
if str(notebook_dir) not in sys.path:
    sys.path.insert(0, str(notebook_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from argo_interp.acoustics import sound_speed_teos10  # noqa: E402
from lib import (  # noqa: E402
    GaussianScale,
    WeightConfig,
    build_candidate_query,
    compute_weight_deltas,
    weighted_profile_mean,
)


data_path = notebook_dir / "data"
cycle_model_cache_path = data_path / "pchip_cycle_models.pkl"
metadata_path = data_path / "sound_speed_uncertainty_product_metadata.json"

detail_path = data_path / "sound_speed_uncertainty_holdout_validation.csv"
summary_path = data_path / "sound_speed_uncertainty_holdout_validation_summary.csv"
run_metadata_path = data_path / "sound_speed_uncertainty_holdout_validation_metadata.json"

target_pressure = np.array([5.0, 35.0, 110.0, 500.0])


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


def rmse(values: pd.Series) -> float:
    return float(np.sqrt(np.nanmean(np.square(values.to_numpy(dtype=float)))))


def finite_count(values: pd.Series) -> int:
    return int(values.notna().sum())


def summarize(detail: pd.DataFrame) -> pd.DataFrame:
    return (
        detail.groupby("pressure_dbar", as_index=False)
        .agg(
            evaluated_cycle_count=("cycle_id", "nunique"),
            finite_temperature_error_count=("temperature_error", finite_count),
            finite_salinity_error_count=("salinity_error", finite_count),
            finite_sound_speed_error_count=("sound_speed_teos10_error", finite_count),
            temperature_rmse=("temperature_error", rmse),
            temperature_mae=("temperature_error", lambda values: float(np.nanmean(np.abs(values)))),
            temperature_bias=("temperature_error", "mean"),
            salinity_rmse=("salinity_error", rmse),
            salinity_mae=("salinity_error", lambda values: float(np.nanmean(np.abs(values)))),
            salinity_bias=("salinity_error", "mean"),
            sound_speed_teos10_rmse=("sound_speed_teos10_error", rmse),
            sound_speed_teos10_mae=(
                "sound_speed_teos10_error",
                lambda values: float(np.nanmean(np.abs(values))),
            ),
            sound_speed_teos10_bias=("sound_speed_teos10_error", "mean"),
            candidate_count_median=("candidate_count", "median"),
            candidate_count_p05=("candidate_count", lambda values: float(values.quantile(0.05))),
            candidate_count_p95=("candidate_count", lambda values: float(values.quantile(0.95))),
            weighted_support_median=("weighted_support", "median"),
            weighted_support_p05=("weighted_support", lambda values: float(values.quantile(0.05))),
            weighted_support_p95=("weighted_support", lambda values: float(values.quantile(0.95))),
            effective_cycle_count_median=("effective_cycle_count", "median"),
            effective_cycle_count_p05=(
                "effective_cycle_count",
                lambda values: float(values.quantile(0.05)),
            ),
            effective_cycle_count_p95=(
                "effective_cycle_count",
                lambda values: float(values.quantile(0.95)),
            ),
        )
        .sort_values("pressure_dbar")
    )


def main() -> None:
    start = time.perf_counter()

    with metadata_path.open() as f:
        product_metadata = json.load(f)

    seconds_per_year = 365.25 * 24 * 60 * 60
    seconds_per_week = 7 * 24 * 60 * 60

    weight_config = WeightConfig(
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
    dist_rad = float(product_metadata["dist_rad"])

    with cycle_model_cache_path.open("rb") as f:
        cycle_model_bundle = pickle.load(f)
    cycle_models = cycle_model_bundle["cycle_models"]
    metadata = cycle_models.metadata()

    interpolates = cycle_models.interpolate(target_pressure)
    temperature_by_cycle = interpolates.temperature.to_numpy(copy=False)
    salinity_by_cycle = interpolates.salinity.to_numpy(copy=False)

    rows: list[dict[str, object]] = []
    skipped_no_candidates = 0

    for position, cycle_id in enumerate(tqdm(metadata.cycle_id, desc="notebook6 holdout")):
        target_latitude = float(metadata.latitude[position])
        target_longitude = float(metadata.longitude[position])
        target_timestamp = metadata.timestamp[position]
        target_platform = metadata.platform_number[position]

        candidate_query = build_candidate_query(
            target_latitude=target_latitude,
            target_longitude=target_longitude,
            dist_rad=dist_rad,
            exclude_platform_number=target_platform,
        )
        candidate_mask = cycle_models.mask(**candidate_query.to_mask_kwargs())
        candidate_count = int(candidate_mask.sum())
        if candidate_count == 0:
            skipped_no_candidates += 1
            continue

        candidate_metadata = cycle_models.metadata(candidate_mask)
        weight_deltas = compute_weight_deltas(
            target_latitude=target_latitude,
            target_longitude=target_longitude,
            target_timestamp=target_timestamp,
            candidate_metadata=candidate_metadata,
        )
        weights = weight_config.joint_weight(weight_deltas)
        candidate_indices = np.flatnonzero(candidate_mask)

        candidate_temperature = temperature_by_cycle[:, candidate_indices]
        candidate_salinity = salinity_by_cycle[:, candidate_indices]
        predicted_temperature = weighted_profile_mean(candidate_temperature, weights)
        predicted_salinity = weighted_profile_mean(candidate_salinity, weights)
        weighted_support = np.isfinite(candidate_temperature) @ weights
        effective_count = effective_cycle_count(candidate_temperature, weights)

        target_temperature = temperature_by_cycle[:, position]
        target_salinity = salinity_by_cycle[:, position]

        pressure = target_pressure
        longitude_array = np.full_like(pressure, target_longitude, dtype=float)
        latitude_array = np.full_like(pressure, target_latitude, dtype=float)

        target_sound_speed = sound_speed_teos10(
            target_salinity,
            target_temperature,
            pressure,
            longitude_array,
            latitude_array,
        )
        predicted_sound_speed = sound_speed_teos10(
            predicted_salinity,
            predicted_temperature,
            pressure,
            longitude_array,
            latitude_array,
        )

        for depth_index, pressure_value in enumerate(target_pressure):
            rows.append(
                {
                    "cycle_id": cycle_id,
                    "platform_number": target_platform,
                    "cycle_number": metadata.cycle_number[position],
                    "direction": metadata.direction[position],
                    "latitude": target_latitude,
                    "longitude": target_longitude,
                    "timestamp": str(pd.Timestamp(target_timestamp)),
                    "pressure_dbar": pressure_value,
                    "target_temperature": target_temperature[depth_index],
                    "predicted_temperature": predicted_temperature[depth_index],
                    "temperature_error": predicted_temperature[depth_index]
                    - target_temperature[depth_index],
                    "target_salinity": target_salinity[depth_index],
                    "predicted_salinity": predicted_salinity[depth_index],
                    "salinity_error": predicted_salinity[depth_index]
                    - target_salinity[depth_index],
                    "target_sound_speed_teos10": target_sound_speed[depth_index],
                    "predicted_sound_speed_teos10": predicted_sound_speed[depth_index],
                    "sound_speed_teos10_error": predicted_sound_speed[depth_index]
                    - target_sound_speed[depth_index],
                    "candidate_count": candidate_count,
                    "weighted_support": weighted_support[depth_index],
                    "effective_cycle_count": effective_count[depth_index],
                    "weight_sum": float(np.sum(weights)),
                }
            )

    detail = pd.DataFrame(rows)
    summary = summarize(detail)

    detail.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)

    elapsed_seconds = time.perf_counter() - start
    run_metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "cycle_model_cache": str(cycle_model_cache_path),
        "product_metadata": product_metadata,
        "target_pressure_dbar": target_pressure.tolist(),
        "validation_design": {
            "name": "notebook6_config_hold_one_float_out",
            "target": "held-out cycle PCHIP estimate at target pressures",
            "candidate_set": "cycles within final spatial prefilter, excluding the held-out platform",
            "weights": "final notebook 6 distance * absolute-time * wrapped-season Gaussian weights",
            "sound_speed_equation": "TEOS-10 via gsw",
        },
        "cycle_count": int(len(metadata)),
        "detail_row_count": int(len(detail)),
        "skipped_cycle_count_no_candidates": int(skipped_no_candidates),
        "detail_csv": str(detail_path),
        "summary_csv": str(summary_path),
    }
    with run_metadata_path.open("w") as f:
        json.dump(run_metadata, f, indent=2, sort_keys=True)
        f.write("\n")

    print(summary.to_string(index=False))
    print(f"\nwrote {detail_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {run_metadata_path}")
    print(f"elapsed_seconds={elapsed_seconds:.2f}")


if __name__ == "__main__":
    main()
