"""Research-only benchmark helpers for the uncertainty-product notebook."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import time
import tracemalloc
from itertools import product
from typing import Sequence

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from argo_interp.uncertainty import SoundSpeedUncertaintyProduct


def package_version(package_name: str) -> str:
    try:
        return importlib_metadata.version(package_name)
    except importlib_metadata.PackageNotFoundError:
        return "not-installed"


def benchmark_grid_points(
    box: Sequence[float | str], lat_resolution_deg: float
) -> list[tuple[float, float]]:
    benchmark_latitudes = np.arange(
        float(box[2]), float(box[3]) + lat_resolution_deg, lat_resolution_deg
    )
    benchmark_longitudes = np.arange(
        float(box[0]), float(box[1]) + lat_resolution_deg, lat_resolution_deg
    )
    return list(product(benchmark_latitudes, benchmark_longitudes))


def run_benchmark_case(
    case: dict[str, float | int | str],
    *,
    product_builder: SoundSpeedUncertaintyProduct,
    box: Sequence[float | str],
    target_pressure: np.ndarray,
    precompute_seconds: float,
) -> dict[str, float | int | str]:
    depth_indices = np.arange(int(case["pressure_count"]))
    query_points = benchmark_grid_points(box, float(case["lat_resolution_deg"]))

    tracemalloc.start()
    start = time.perf_counter()
    records = []
    for latitude, longitude in tqdm(query_points, desc=str(case["case_id"]), leave=False):
        records.extend(
            product_builder.query(
                latitude=latitude,
                longitude=longitude,
                depth_indices=depth_indices,
            ).to_dict("records")
        )
    elapsed_seconds = time.perf_counter() - start
    _current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    case_product = pd.DataFrame.from_records(records)
    finite_sigma_count = (
        int(case_product["sigma_sound_speed_teos10"].notna().sum())
        if not case_product.empty
        else 0
    )

    return {
        "case_id": str(case["case_id"]),
        "lat_resolution_deg": float(case["lat_resolution_deg"]),
        "pressure_count": int(case["pressure_count"]),
        "pressure_dbar_values": "|".join(
            str(value) for value in target_pressure[depth_indices]
        ),
        "query_point_count": len(query_points),
        "output_row_count": len(case_product),
        "finite_sigma_count": finite_sigma_count,
        "wall_time_seconds": elapsed_seconds,
        "precompute_seconds": precompute_seconds,
        "query_points_per_second": len(query_points) / elapsed_seconds
        if elapsed_seconds
        else np.nan,
        "rows_per_second": len(case_product) / elapsed_seconds
        if elapsed_seconds
        else np.nan,
        "peak_traced_memory_mb": peak_memory / (1024**2),
    }
