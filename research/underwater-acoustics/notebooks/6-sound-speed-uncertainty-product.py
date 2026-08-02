# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     notebook_metadata_filter: jupytext,kernelspec,language_info
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: argo-data-interpolation (.venv)
#     language: python
#     name: argo-data-interpolation
#   language_info:
#     codemirror_mode:
#       name: ipython
#       version: 3
#     file_extension: .py
#     mimetype: text/x-python
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#     version: 3.13.5
# ---

# %% [markdown]
# # Sound-Speed Uncertainty Product
#
# This notebook is the OCEANS 2026 paper-support uncertainty build. It starts a
# new path after notebook `5`: notebook `5` remains the deterministic model-build
# artifact, while this notebook produces the figure-ready uncertainty table.
#
# The output unit is one row per query point and target pressure/depth. The table
# carries temperature and salinity point estimates, componentized T/S variances,
# GSW/TEOS-10 sound-speed estimates, finite-difference sound-speed partial
# derivatives, propagated sound-speed variances, support diagnostics, and 110 m
# decomposition columns for paper figures.

# %%
from __future__ import annotations

import json
import pickle
import sys
import time
import tracemalloc
from itertools import product
from pathlib import Path

import importlib.metadata as importlib_metadata
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable
from tqdm.auto import tqdm

from argo_interp.uncertainty import (
    GaussianScale,
    SoundSpeedUncertaintyProduct,
    SoundSpeedUncertaintyConfig,
    WeightConfig,
    depth_summary,
    estimate_depthwise_spatial_variance as estimate_depthwise_spatial_variance_package,
)
from argo_interp.cycle.adapter import PchipAdapter
from argo_interp.cycle.config import ModelSettings
from argo_interp.cycle.domain import ModelData, ModelMeta
from argo_interp.cycle.model import Model
from argo_interp.data.data_filter import data_filter
from argo_interp.model import CycleModels

# %% [markdown]
# ## Configuration
#
# The horizontal grid and target depths follow the notebook `5` model-build
# defaults. The anchor date is fixed here for reproducibility. The current
# weight configuration uses distance, absolute time, and wrapped seasonal
# weighting.

# %%
notebook_dir = Path.cwd()
if not (notebook_dir / "lib").exists():
    notebook_dir = Path("research/underwater-acoustics/notebooks")

data_path = notebook_dir / "data"
chart_path = data_path / "charts"
cartopy_data_path = data_path / "cartopy"
data_path.mkdir(exist_ok=True, parents=True)
chart_path.mkdir(exist_ok=True, parents=True)
cartopy_data_path.mkdir(exist_ok=True, parents=True)
cartopy.config["data_dir"] = str(cartopy_data_path)

box = [
    80,
    99,
    6,
    23,
    0,
    750,
    "2011-01-01",
    "2020-12-31",
]

target_pressure = np.array([5.0, 35.0, 110.0, 500.0])
anchor_time = np.datetime64("2015-07-01")
analysis_date_label = str(anchor_time)

lat_resolution = 1e-1
lon_resolution = 1e-1
lat_array = np.arange(box[2], box[3] + lat_resolution, lat_resolution)
lon_array = np.arange(box[0], box[1] + lon_resolution, lon_resolution)
lat_lon_product = list(product(lat_array, lon_array))

distance_kernel_sigma_deg = 1.0 / 3.0
candidate_radius_sigma = 3.0
dist_rad = distance_kernel_sigma_deg * candidate_radius_sigma

seconds_per_year = 365.25 * 24 * 60 * 60
seconds_per_week = 7 * 24 * 60 * 60

year_stdev = 3.0
season_weeks = 8
season_week_stdev = 3.0

use_distance_weight = True
use_time_weight = True
use_season_weight = True
sensor_support_tau = 40.0

weight_config = WeightConfig(
    distance=GaussianScale(distance_kernel_sigma_deg),
    time=GaussianScale(year_stdev * seconds_per_year),
    season=GaussianScale.from_border(season_weeks * seconds_per_week, season_week_stdev),
    use_distance=use_distance_weight,
    use_time=use_time_weight,
    use_season=use_season_weight,
)

uncertainty_config = SoundSpeedUncertaintyConfig(
    target_pressure=target_pressure,
    weight_config=weight_config,
    anchor_time=anchor_time,
    candidate_radius=dist_rad,
    distance_metric="planar_degrees",
    sensor_support_tau=sensor_support_tau,
)

weighting_cache_metadata = {
    "anchor_time": str(anchor_time),
    "distance_kernel_sigma_deg": distance_kernel_sigma_deg,
    "candidate_radius_sigma": candidate_radius_sigma,
    "dist_rad": dist_rad,
    "year_stdev": year_stdev,
    "season_weeks": season_weeks,
    "season_week_stdev": season_week_stdev,
    "use_distance_weight": use_distance_weight,
    "use_time_weight": use_time_weight,
    "use_season_weight": use_season_weight,
    "sensor_support_tau": sensor_support_tau,
}

argo_data_path = data_path / "argo_data.pkl"
cycle_model_cache_path = data_path / "pchip_cycle_models.pkl"
spatial_variance_path = data_path / "sound_speed_uncertainty_spatial_variance.pkl"
spatial_variance_metadata_path = data_path / "sound_speed_uncertainty_spatial_variance_metadata.json"
uncertainty_product_path = data_path / "sound_speed_uncertainty_product.pkl"
uncertainty_product_metadata_path = data_path / "sound_speed_uncertainty_product_metadata.json"
uncertainty_product_csv_path = data_path / "sound_speed_uncertainty_product.csv"
uncertainty_product_110m_csv_path = data_path / "sound_speed_uncertainty_product_110m.csv"
uncertainty_depth_summary_csv_path = data_path / "sound_speed_uncertainty_depth_summary.csv"
benchmark_path = data_path / "sound_speed_uncertainty_benchmark.csv"
benchmark_metadata_path = data_path / "sound_speed_uncertainty_benchmark_metadata.json"


def cache_metadata_matches(metadata_path: Path, expected_metadata: dict[str, object]) -> bool:
    if not metadata_path.exists():
        return False
    with metadata_path.open() as f:
        return json.load(f) == expected_metadata


def write_cache_metadata(metadata_path: Path, metadata: dict[str, object]) -> None:
    with metadata_path.open("w") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
        f.write("\n")

# %% [markdown]
# ## Load Argo Data When Rebuilding Cycle Models
#
# The uncertainty product uses the cached PCHIP cycle-model bundle when present.
# Raw Argo data is loaded only when that bundle must be rebuilt.

# %%
def load_filtered_argo_data():
    if argo_data_path.exists():
        with argo_data_path.open("rb") as f:
            ds = pickle.load(f)
    else:
        from argo_interp.data.get_data import get_data

        ds = get_data(box, progress=True)
        with argo_data_path.open("wb") as f:
            pickle.dump(ds, f)

    ds_filters = [
        ds["PRES_QC"].isin([1, 2]),
        ds["TEMP_QC"].isin([1, 2]),
        ds["PSAL_QC"].isin([1, 2]),
    ]
    return data_filter(ds, ds_filters)

# %% [markdown]
# ## Build or Load Per-Cycle Models
#
# The cached model bundle is specific to this notebook's PCHIP cycle model
# backbone. Delete `data/pchip_cycle_models.pkl` to force a rebuild after model
# or filtering changes.

# %%
settings = ModelSettings(n_folds=5)


def build_cycle_models(filtered_ds, model_settings):
    models = {}
    models_data = {}

    cycles = len(
        filtered_ds[["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"]]
        .to_dataframe()
        .drop_duplicates()
    )
    grouped = filtered_ds.groupby(["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"])

    for (platform_number, cycle_number, direction), cycle_ds in tqdm(grouped, total=cycles):
        pressure = cycle_ds["PRES"].values
        temperature = cycle_ds["TEMP"].values
        salinity = cycle_ds["PSAL"].values

        if cycle_ds.sizes["N_POINTS"] < 3:
            continue

        model_data = ModelData(
            pressure=pressure,
            temperature=temperature,
            salinity=salinity,
        ).clean_duplicates("mean")

        model_meta = ModelMeta(
            platform_number=str(int(platform_number)),
            cycle_number=str(int(cycle_number)),
            direction=direction,
            latitude=cycle_ds["LATITUDE"].values[0],
            longitude=cycle_ds["LONGITUDE"].values[0],
            timestamp=cycle_ds["TIME"].values[0],
            profile_pressure=(pressure.min(), pressure.max()),
        )

        model = Model.build(model_meta, model_data, PchipAdapter, model_settings)
        models[model_meta.cycle_id] = model
        models_data[model_meta.cycle_id] = model_data

    return CycleModels(models), models_data


if cycle_model_cache_path.exists():
    with cycle_model_cache_path.open("rb") as f:
        cycle_model_bundle = pickle.load(f)
    cycle_models = cycle_model_bundle["cycle_models"]
    models_data = cycle_model_bundle["models_data"]
else:
    ds = load_filtered_argo_data()
    cycle_models, models_data = build_cycle_models(ds, settings)
    with cycle_model_cache_path.open("wb") as f:
        pickle.dump({"cycle_models": cycle_models, "models_data": models_data}, f)

all_metadata = cycle_models.metadata()
len(all_metadata)

# %% [markdown]
# ## Spatial Variance Bucket
#
# The per-cycle model variance covers vertical reconstruction within a cycle.
# This section estimates the separate spatial interpolation bucket by predicting
# each target cycle from neighboring cycles on the same target pressure grid.
# The target values are the held-out cycle model values at those pressures, so
# the residual primarily measures local-window interpolation rather than raw
# vertical sampling noise.

spatial_variance_cache_valid = spatial_variance_path.exists() and cache_metadata_matches(
    spatial_variance_metadata_path,
    weighting_cache_metadata,
)

if spatial_variance_cache_valid:
    with spatial_variance_path.open("rb") as f:
        spatial_variance = pickle.load(f)
else:
    spatial_variance = estimate_depthwise_spatial_variance_package(
        cycle_models=cycle_models,
        config=uncertainty_config,
    )
    with spatial_variance_path.open("wb") as f:
        pickle.dump(spatial_variance, f)
    write_cache_metadata(spatial_variance_metadata_path, weighting_cache_metadata)

spatial_variance

uncertainty_product_builder = SoundSpeedUncertaintyProduct(
    cycle_models=cycle_models,
    spatial_variance=spatial_variance,
    config=uncertainty_config,
)

# %% [markdown]
# ## Precompute Cycle-Level Target-Pressure Terms
#
# The query product evaluates the same target pressure grid at many lat/lon
# points. Precomputing per-cycle estimates and variance components once keeps
# the full-grid loop focused on spatial support, weighting, and aggregation.

# %%
uncertainty_product_cache_valid = uncertainty_product_path.exists() and cache_metadata_matches(
    uncertainty_product_metadata_path,
    weighting_cache_metadata,
)

def ensure_cycle_target_terms() -> None:
    uncertainty_product_builder.precompute_cycle_terms()

# %% [markdown]
# ## Query-Point Uncertainty Product
#
# Component variances are aggregated with squared normalized weights. The
# spatial bucket is added after the weighted per-cycle component buckets and
# before sound-speed propagation. The T-S covariance term is intentionally zero:
# no cross term is included in the sound-speed variance.

# %%
def build_uncertainty_rows(
    lat: float,
    lon: float,
    depth_indices: np.ndarray | None = None,
) -> list[dict[str, float]]:
    return uncertainty_product_builder.query(
        latitude=lat,
        longitude=lon,
        depth_indices=depth_indices,
    ).to_dict("records")


if uncertainty_product_cache_valid:
    uncertainty_product = pd.read_pickle(uncertainty_product_path)
else:
    records = []
    for lat, lon in tqdm(lat_lon_product):
        records.extend(build_uncertainty_rows(lat, lon))

    uncertainty_product = pd.DataFrame.from_records(records)

uncertainty_product

# %% [markdown]
# ## Export Paper-Support Tables
#
# The full table keeps every target pressure. The 110 m CSV is the immediate
# figure input for the decomposition panels.

# %%
uncertainty_product.to_pickle(uncertainty_product_path)
write_cache_metadata(uncertainty_product_metadata_path, weighting_cache_metadata)
uncertainty_product.to_csv(uncertainty_product_csv_path, index=False)

uncertainty_product_110m = uncertainty_product.loc[
    np.isclose(uncertainty_product["depth_m"], 110.0)
].copy()
uncertainty_product_110m.to_csv(uncertainty_product_110m_csv_path, index=False)

uncertainty_depth_summary = depth_summary(uncertainty_product)
uncertainty_depth_summary.to_csv(uncertainty_depth_summary_csv_path, index=False)

uncertainty_product_110m.describe(include="all")

# %% [markdown]
# ## Cached-Input Product Benchmark
#
# This benchmark measures the paper-support product-build path after the
# cycle-model and spatial-variance caches already exist. It does not measure raw
# Argo download, per-cycle model rebuild, or spatial-validation recomputation.
# Those are separate costs. The benchmark matrix varies horizontal grid step and
# target-pressure count, records wall time and traced Python peak memory, and
# writes a small CSV/JSON artifact for handoff.

# %%
benchmark_cases = [
    {"case_id": "grid_1p0_depth1", "lat_resolution_deg": 1.0, "pressure_count": 1},
    {"case_id": "grid_1p0_depth4", "lat_resolution_deg": 1.0, "pressure_count": 4},
    {"case_id": "grid_0p5_depth1", "lat_resolution_deg": 0.5, "pressure_count": 1},
    {"case_id": "grid_0p5_depth4", "lat_resolution_deg": 0.5, "pressure_count": 4},
    {"case_id": "grid_0p25_depth4", "lat_resolution_deg": 0.25, "pressure_count": 4},
    {"case_id": "grid_0p1_depth4", "lat_resolution_deg": 0.1, "pressure_count": 4},
]


def package_version(package_name: str) -> str:
    try:
        return importlib_metadata.version(package_name)
    except importlib_metadata.PackageNotFoundError:
        return "not-installed"


benchmark_metadata = {
    "scope": "cached cycle models + cached spatial variance product-build benchmark",
    "anchor_time": str(anchor_time),
    "target_pressure": target_pressure.tolist(),
    "weighting": weighting_cache_metadata,
    "cases": benchmark_cases,
    "versions": {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "gsw": package_version("gsw"),
        "cartopy": cartopy.__version__,
    },
}


def benchmark_grid_points(lat_resolution_deg: float) -> list[tuple[float, float]]:
    benchmark_latitudes = np.arange(box[2], box[3] + lat_resolution_deg, lat_resolution_deg)
    benchmark_longitudes = np.arange(box[0], box[1] + lat_resolution_deg, lat_resolution_deg)
    return list(product(benchmark_latitudes, benchmark_longitudes))


def run_benchmark_case(
    case: dict[str, float | int | str],
    *,
    precompute_seconds: float,
) -> dict[str, float | int | str]:
    depth_indices = np.arange(int(case["pressure_count"]))
    query_points = benchmark_grid_points(float(case["lat_resolution_deg"]))

    tracemalloc.start()
    start = time.perf_counter()
    records = []
    for lat, lon in tqdm(query_points, desc=str(case["case_id"]), leave=False):
        records.extend(build_uncertainty_rows(lat, lon, depth_indices=depth_indices))
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
        "pressure_dbar_values": "|".join(str(value) for value in target_pressure[depth_indices]),
        "query_point_count": len(query_points),
        "output_row_count": len(case_product),
        "finite_sigma_count": finite_sigma_count,
        "wall_time_seconds": elapsed_seconds,
        "precompute_seconds": precompute_seconds,
        "query_points_per_second": len(query_points) / elapsed_seconds if elapsed_seconds else np.nan,
        "rows_per_second": len(case_product) / elapsed_seconds if elapsed_seconds else np.nan,
        "peak_traced_memory_mb": peak_memory / (1024**2),
    }


benchmark_cache_valid = benchmark_path.exists() and cache_metadata_matches(
    benchmark_metadata_path,
    benchmark_metadata,
)

if benchmark_cache_valid:
    benchmark_results = pd.read_csv(benchmark_path)
else:
    precompute_start = time.perf_counter()
    ensure_cycle_target_terms()
    precompute_seconds = time.perf_counter() - precompute_start
    benchmark_results = pd.DataFrame(
        [
            run_benchmark_case(case, precompute_seconds=precompute_seconds)
            for case in benchmark_cases
        ]
    )
    benchmark_results.to_csv(benchmark_path, index=False)
    write_cache_metadata(benchmark_metadata_path, benchmark_metadata)

benchmark_results

# %% [markdown]
# ## Figure-Ready 110 m Matrices
#
# These pivots are intentionally separated from plotting so the paper figure
# code can choose the final visual grammar without recomputing the uncertainty
# product.

# %%
plot_fields = [
    "sound_speed_teos10",
    "sigma_sound_speed_teos10",
    "var_sound_speed_teos10_sensor_bucket",
    "var_sound_speed_teos10_model_bucket",
    "W_raw",
    "W_display",
]

chart_latitudes = pd.Index(lat_array, name="latitude")
chart_longitudes = pd.Index(lon_array, name="longitude")

figure_matrices_110m = {
    field: uncertainty_product_110m.pivot(index="latitude", columns="longitude", values=field).reindex(
        index=chart_latitudes,
        columns=chart_longitudes,
    )
    for field in plot_fields
}

figure_matrices_110m["sigma_sound_speed_teos10"].mean().mean()

# %% [markdown]
# ## 110 m Paper-Support Charts
#
# The five chart exports match the immediate OCEANS 2026 decomposition need:
# point estimate, propagated sigma, standalone support, point estimate with
# support-break contours, and sigma with support-break contours.
#
# Sigma charts use the local 110 m `p01..p99` value range rather than anchoring
# at zero. The sound-speed W chart overlays exploratory `W_raw` contours. The
# sigma W chart uses the same raw-support contour levels and legend treatment.
# The standalone support chart uses raw `W` values with color anchors at the
# raw support region midpoints. Its map colors and colorbar axis use the same
# log-spaced raw `W` transform for readability, and it overlays the same raw
# `W=6` and `W=30` contours used by the sound-speed contour chart. Exact finite
# zero support is rendered transparent; other finite support values are opaque.
# The heatmaps use bilinear display interpolation to avoid visual blockiness
# from the 0.1-degree plotting grid; this does not change the cached product.

# %%
heatmap_interpolation = "bilinear"


def chart_title(title: str) -> str:
    return f"{title}\nAnalysis date: {analysis_date_label}"


def matrix_extent(matrix: pd.DataFrame) -> tuple[float, float, float, float]:
    latitudes = matrix.index.to_numpy(dtype=float)
    longitudes = matrix.columns.to_numpy(dtype=float)
    lat_step = float(np.nanmedian(np.diff(latitudes)))
    lon_step = float(np.nanmedian(np.diff(longitudes)))
    return (
        float(longitudes[0] - lon_step / 2),
        float(longitudes[-1] + lon_step / 2),
        float(latitudes[0] - lat_step / 2),
        float(latitudes[-1] + lat_step / 2),
    )


def add_land_overlay(ax: plt.Axes, *, grid_alpha: float = 0.6) -> None:
    ax.add_feature(cfeature.LAND, facecolor="0.78", edgecolor="none", zorder=3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.55, edgecolor="0.15", zorder=4)
    ax.set_extent((box[0], box[1], box[2], box[3]), crs=ccrs.PlateCarree())
    gridliner = ax.gridlines(
        draw_labels=True,
        linewidth=0.25,
        color="white",
        alpha=grid_alpha,
        linestyle="-",
        zorder=5,
    )
    gridliner.top_labels = False
    gridliner.right_labels = False


def save_figure(fig: plt.Figure, stem: str) -> dict[str, Path]:
    paths = {
        "png": chart_path / f"{stem}.png",
        "svg": chart_path / f"{stem}.svg",
    }
    for output_path in paths.values():
        fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    return paths


def plot_matrix(
    matrix: pd.DataFrame,
    *,
    title: str,
    cbar_label: str,
    cmap: str | mcolors.Colormap,
    vmin: float | None = None,
    vmax: float | None = None,
    fill_missing: float | None = None,
    grid_alpha: float = 0.6,
) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(9, 7), subplot_kw={"projection": ccrs.PlateCarree()})
    fig.patch.set_facecolor("white")
    ax.set_facecolor("0.94")
    values = matrix.to_numpy(dtype=float)
    image_values = (
        np.nan_to_num(values, nan=fill_missing)
        if fill_missing is not None
        else np.ma.masked_invalid(values)
    )

    image = ax.imshow(
        image_values,
        origin="lower",
        extent=matrix_extent(matrix),
        aspect="auto",
        interpolation=heatmap_interpolation,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    add_land_overlay(ax, grid_alpha=grid_alpha)

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label(cbar_label)
    fig.tight_layout()
    return fig, ax


def add_support_contours(
    ax: plt.Axes,
    support: pd.DataFrame,
    *,
    contour_levels: list[float],
    contour_labels: list[str] | None = None,
    contour_value_label: str = "W",
    contour_value_precision: int = 3,
    legend_loc: str | None = None,
) -> None:
    support_values = np.ma.masked_invalid(support.to_numpy(dtype=float))
    longitudes = support.columns.to_numpy(dtype=float)
    latitudes = support.index.to_numpy(dtype=float)
    contour_linestyles = ["--", "-", "-."]
    contour_linewidths = [1.15, 1.45, 1.25]
    legend_handles = []
    for index, level in enumerate(contour_levels):
        label = (
            contour_labels[index]
            if contour_labels is not None
            else f"{contour_value_label}={level:.{contour_value_precision}f}"
        )
        linestyle = contour_linestyles[index % len(contour_linestyles)]
        linewidth = contour_linewidths[index % len(contour_linewidths)]
        contour = ax.contour(
            longitudes,
            latitudes,
            support_values,
            levels=[level],
            colors="#111827",
            linewidths=linewidth,
            linestyles=linestyle,
            transform=ccrs.PlateCarree(),
            zorder=2,
        )
        contour.set_path_effects(
            [
                path_effects.Stroke(linewidth=linewidth + 1.7, foreground="white"),
                path_effects.Normal(),
            ]
        )
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color="#111827",
                linewidth=linewidth,
                linestyle=linestyle,
                path_effects=[
                    path_effects.Stroke(linewidth=linewidth + 1.7, foreground="white"),
                    path_effects.Normal(),
                ],
                label=label,
            )
        )
    if legend_loc is not None:
        ax.legend(
            handles=legend_handles,
            loc=legend_loc,
            frameon=True,
            framealpha=0.85,
            facecolor="white",
            edgecolor="0.35",
            fontsize=8,
        )


def plot_matrix_with_support_contours(
    matrix: pd.DataFrame,
    support: pd.DataFrame,
    *,
    title: str,
    cbar_label: str,
    cmap: str | mcolors.Colormap,
    vmin: float | None = None,
    vmax: float | None = None,
    contour_levels: list[float],
    contour_labels: list[str] | None = None,
    contour_value_label: str = "W",
    contour_value_precision: int = 3,
    legend_loc: str = "lower left",
    grid_alpha: float = 0.6,
) -> tuple[plt.Figure, plt.Axes]:
    if not matrix.index.equals(support.index) or not matrix.columns.equals(support.columns):
        raise ValueError("matrix and support must share identical index and columns")

    values = matrix.to_numpy(dtype=float)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        raise ValueError("matrix must contain at least one finite value")

    if vmin is None:
        vmin = float(finite_values.min())
    if vmax is None:
        vmax = float(finite_values.max())

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    image_values = np.ma.masked_invalid(values)

    fig, ax = plt.subplots(figsize=(9, 7), subplot_kw={"projection": ccrs.PlateCarree()})
    fig.patch.set_facecolor("white")
    ax.set_facecolor("0.94")

    image = ax.imshow(
        image_values,
        origin="lower",
        extent=matrix_extent(matrix),
        aspect="auto",
        interpolation=heatmap_interpolation,
        cmap=cmap,
        norm=norm,
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    add_support_contours(
        ax,
        support,
        contour_levels=contour_levels,
        contour_labels=contour_labels,
        contour_value_label=contour_value_label,
        contour_value_precision=contour_value_precision,
        legend_loc=legend_loc,
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    add_land_overlay(ax, grid_alpha=grid_alpha)

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label(cbar_label)

    fig.tight_layout()
    return fig, ax


def plot_support_matrix(
    matrix: pd.DataFrame,
    *,
    title: str,
    cbar_label: str,
    cmap: mcolors.Colormap,
    norm: mcolors.Normalize,
    colorbar_ticks: list[float],
    colorbar_scale: str = "linear",
    cluster_labels: list[tuple[str, float]] | None = None,
    contour_levels: list[float] | None = None,
    contour_labels: list[str] | None = None,
    contour_value_label: str = "W",
    contour_value_precision: int = 3,
    contour_legend_loc: str | None = None,
    transparent_threshold: float = 0.0,
    grid_alpha: float = 1.0,
    interpolation: str = "nearest",
) -> tuple[plt.Figure, plt.Axes]:
    values = matrix.to_numpy(dtype=float)
    rgba = cmap(norm(values))

    missing_mask = ~np.isfinite(values)
    zero_mask = np.isfinite(values) & (values <= transparent_threshold)
    finite_nonzero_mask = np.isfinite(values) & (values > transparent_threshold)

    rgba[missing_mask] = mcolors.to_rgba("white", alpha=1.0)
    rgba[zero_mask, 3] = 0.0
    rgba[finite_nonzero_mask, 3] = 1.0

    fig, ax = plt.subplots(figsize=(9, 7), subplot_kw={"projection": ccrs.PlateCarree()})
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.imshow(
        rgba,
        origin="lower",
        extent=matrix_extent(matrix),
        aspect="auto",
        interpolation=interpolation,
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    if contour_levels is not None:
        add_support_contours(
            ax,
            matrix,
            contour_levels=contour_levels,
            contour_labels=contour_labels,
            contour_value_label=contour_value_label,
            contour_value_precision=contour_value_precision,
            legend_loc=contour_legend_loc,
        )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    add_land_overlay(ax, grid_alpha=grid_alpha)

    scalar_mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    scalar_mappable.set_array([])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3.4%", pad=0.55, axes_class=plt.Axes)
    if colorbar_scale == "log":
        colorbar_positive_ticks = [tick for tick in colorbar_ticks if tick > 0]
        colorbar_vmin = min(colorbar_positive_ticks)
        colorbar_vmax = max(colorbar_positive_ticks)
        colorbar_edges = np.geomspace(colorbar_vmin, colorbar_vmax, 256)
        colorbar_centers = np.sqrt(colorbar_edges[:-1] * colorbar_edges[1:])
        cax.pcolormesh(
            [0.0, 1.0],
            colorbar_edges,
            colorbar_centers[:, np.newaxis],
            cmap=cmap,
            norm=norm,
            shading="flat",
        )
        cax.set_yscale("log")
        cax.set_ylim(colorbar_vmin, colorbar_vmax)
        cax.set_xlim(0.0, 1.0)
        cax.set_xticks([])
        cax.set_yticks(colorbar_ticks)
        cax.set_ylabel(cbar_label)
        colorbar_ax = cax
    else:
        colorbar = fig.colorbar(scalar_mappable, cax=cax, ticks=colorbar_ticks)
        colorbar.set_label(cbar_label)
        colorbar_ax = colorbar.ax
    colorbar_ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_raw_support_tick))
    colorbar_ax.minorticks_off()
    if cluster_labels:
        colorbar_ax.set_ylabel("")
        colorbar_ax.set_title(cbar_label, pad=8)
        colorbar_ax.yaxis.set_ticks_position("left")
        colorbar_ax.yaxis.set_label_position("left")
        transform = colorbar_ax.get_yaxis_transform()
        for label, value in cluster_labels:
            colorbar_ax.text(
                1.45,
                value,
                label,
                transform=transform,
                rotation=90,
                ha="center",
                va="center",
                clip_on=False,
            )
    fig.tight_layout()
    return fig, ax


def format_raw_support_tick(value: float, _position: int | None = None) -> str:
    if not np.isfinite(value):
        return ""
    if value >= 100:
        return f"{value:.1f}"
    if value >= 1:
        return f"{value:.2g}"
    return f"{value:.2g}"


def support_region_cmap(
    *,
    low_anchor: float,
    mid_anchor: float,
    high_anchor: float,
    missing: str = "white",
) -> mcolors.Colormap:
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "support_region",
        [
            (0.0, "#14081f"),
            (low_anchor, "#2457d6"),
            (mid_anchor, "#ff8b1a"),
            (high_anchor, "#2fca62"),
            (1.0, "#b7f45b"),
        ],
        N=256,
    )
    cmap = cmap.with_extremes(
        bad=missing,
        under="#14081f",
        over="#b7f45b",
    )
    cmap.set_bad(color=missing, alpha=1.0)
    return cmap


# %%
sound_speed_110m = figure_matrices_110m["sound_speed_teos10"]
sigma_sound_speed_110m = figure_matrices_110m["sigma_sound_speed_teos10"]
support_raw_110m = figure_matrices_110m["W_raw"]

support_transparent_threshold = 0.0
support_raw_finite_values = support_raw_110m.to_numpy(dtype=float)
support_raw_finite_values = support_raw_finite_values[np.isfinite(support_raw_finite_values)]
support_raw_positive_values = support_raw_finite_values[support_raw_finite_values > support_transparent_threshold]
support_raw_min_positive = float(np.nanmin(support_raw_positive_values))
support_raw_log_floor = 1.0
support_raw_vmax = float(np.nanmax(support_raw_finite_values))
support_raw_breaks = [support_raw_log_floor, 6.0, 30.0, support_raw_vmax]
support_cluster_labels = [
    ("Low", np.sqrt(support_raw_breaks[0] * support_raw_breaks[1])),
    ("Mid", np.sqrt(support_raw_breaks[1] * support_raw_breaks[2])),
    ("High", np.sqrt(support_raw_breaks[2] * support_raw_breaks[3])),
]
support_color_anchor_values = [value for _, value in support_cluster_labels]
support_norm = mcolors.LogNorm(vmin=support_raw_log_floor, vmax=support_raw_vmax)
support_raw_anchor_positions = [float(support_norm(value)) for value in support_color_anchor_values]
support_cmap = support_region_cmap(
    low_anchor=support_raw_anchor_positions[0],
    mid_anchor=support_raw_anchor_positions[1],
    high_anchor=support_raw_anchor_positions[2],
)
support_contour_levels = [6.0, 30.0]
support_contour_labels = ["Low/Mid boundary (W=6)", "Mid/High boundary (W=30)"]
sound_speed_contour_cmap = mcolors.LinearSegmentedColormap.from_list(
    "sound_speed_contour_hue",
    ["#3056ff", "#00c4df", "#19e967", "#e7ea19", "#ff9700", "#ff2b2b"],
)

sound_speed_limits = (
    float(np.nanquantile(sound_speed_110m.to_numpy(dtype=float), 0.01)),
    float(np.nanquantile(sound_speed_110m.to_numpy(dtype=float), 0.99)),
)
sigma_limits = (
    float(np.nanquantile(sigma_sound_speed_110m.to_numpy(dtype=float), 0.01)),
    float(np.nanquantile(sigma_sound_speed_110m.to_numpy(dtype=float), 0.99)),
)

chart_exports = {}

fig, ax = plot_matrix(
    sound_speed_110m,
    title=chart_title("Bay of Bengal TEOS-10 Sound Speed at 110 m"),
    cbar_label="Sound speed (m/s)",
    cmap=sound_speed_contour_cmap,
    vmin=sound_speed_limits[0],
    vmax=sound_speed_limits[1],
)
chart_exports["sound_speed_teos10_110m"] = save_figure(fig, "sound_speed_teos10_110m")

fig, ax = plot_matrix(
    sigma_sound_speed_110m,
    title=chart_title("Bay of Bengal Sound-Speed Sigma at 110 m"),
    cbar_label="Sigma (m/s)",
    cmap="magma",
    vmin=sigma_limits[0],
    vmax=sigma_limits[1],
)
chart_exports["sigma_sound_speed_teos10_110m"] = save_figure(fig, "sigma_sound_speed_teos10_110m")

fig, ax = plot_support_matrix(
    support_raw_110m,
    title=chart_title("Bay of Bengal Raw Support Weight at 110 m"),
    cbar_label="W raw",
    cmap=support_cmap,
    norm=support_norm,
    colorbar_ticks=support_raw_breaks,
    colorbar_scale="log",
    cluster_labels=support_cluster_labels,
    contour_levels=support_contour_levels,
    contour_labels=support_contour_labels,
    contour_value_label="W raw",
    contour_value_precision=2,
    contour_legend_loc="upper left",
    transparent_threshold=support_transparent_threshold,
    grid_alpha=1.0,
    interpolation="nearest",
)
chart_exports["w_raw_110m"] = save_figure(fig, "w_raw_110m")

fig, ax = plot_matrix_with_support_contours(
    sound_speed_110m,
    support_raw_110m,
    title=chart_title("Bay of Bengal TEOS-10 Sound Speed at 110 m with Raw W Contours"),
    cbar_label="Sound speed (m/s)",
    cmap=sound_speed_contour_cmap,
    vmin=sound_speed_limits[0],
    vmax=sound_speed_limits[1],
    contour_levels=support_contour_levels,
    contour_labels=support_contour_labels,
    contour_value_label="W raw",
    contour_value_precision=2,
    legend_loc="upper left",
)
chart_exports["sound_speed_teos10_w_contours_110m"] = save_figure(
    fig,
    "sound_speed_teos10_w_contours_110m",
)

fig, ax = plot_matrix_with_support_contours(
    sigma_sound_speed_110m,
    support_raw_110m,
    title=chart_title("Bay of Bengal Sound-Speed Sigma at 110 m with Raw W Contours"),
    cbar_label="Sigma (m/s)",
    cmap="magma",
    vmin=sigma_limits[0],
    vmax=sigma_limits[1],
    contour_levels=support_contour_levels,
    contour_labels=support_contour_labels,
    contour_value_label="W raw",
    contour_value_precision=2,
    legend_loc="upper left",
)
chart_exports["sigma_sound_speed_teos10_w_contours_110m"] = save_figure(
    fig,
    "sigma_sound_speed_teos10_w_contours_110m",
)

chart_exports

# %% [markdown]
# ## Output Paths

# %%
{
    "full_uncertainty_product_pickle": uncertainty_product_path,
    "full_uncertainty_product_csv": uncertainty_product_csv_path,
    "uncertainty_product_110m_csv": uncertainty_product_110m_csv_path,
    "uncertainty_depth_summary_csv": uncertainty_depth_summary_csv_path,
    "benchmark_csv": benchmark_path,
    "benchmark_metadata_json": benchmark_metadata_path,
    "spatial_variance_pickle": spatial_variance_path,
    "cycle_model_cache": cycle_model_cache_path,
    "chart_exports": chart_exports,
}
