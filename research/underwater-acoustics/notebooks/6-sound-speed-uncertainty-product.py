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

import pickle
import sys
import time
from itertools import product
from pathlib import Path

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import cartopy
from tqdm.auto import tqdm

from argo_interp.uncertainty import (
    GaussianScale,
    SoundSpeedUncertaintyProduct,
    SoundSpeedUncertaintyConfig,
    WeightConfig,
    depth_summary,
    estimate_depthwise_spatial_variance as estimate_depthwise_spatial_variance_package,
)
from argo_interp.cycle.config import ModelSettings

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

if str(notebook_dir) not in sys.path:
    sys.path.insert(0, str(notebook_dir))

from lib.benchmarking import package_version, run_benchmark_case
from lib.plotting import (
    chart_title,
    plot_matrix,
    plot_matrix_with_support_contours,
    plot_support_matrix,
    save_figure,
    support_region_cmap,
)
from lib.product_support import (
    build_cycle_models,
    cache_metadata_matches,
    load_filtered_argo_data,
    write_cache_metadata,
)

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


# %% [markdown]
# ## Load Argo Data When Rebuilding Cycle Models
#
# The uncertainty product uses the cached PCHIP cycle-model bundle when present.
# Raw Argo data is loaded only when that bundle must be rebuilt.

# %%
# %% [markdown]
# ## Build or Load Per-Cycle Models
#
# The cached model bundle is specific to this notebook's PCHIP cycle model
# backbone. Delete `data/pchip_cycle_models.pkl` to force a rebuild after model
# or filtering changes.

# %%
settings = ModelSettings(n_folds=5)


if cycle_model_cache_path.exists():
    with cycle_model_cache_path.open("rb") as f:
        cycle_model_bundle = pickle.load(f)
    cycle_models = cycle_model_bundle["cycle_models"]
    models_data = cycle_model_bundle["models_data"]
else:
    ds = load_filtered_argo_data(argo_data_path, box)
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

# %%
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

# %% [markdown]
# ## Query-Point Uncertainty Product
#
# Component variances are aggregated with squared normalized weights. The
# spatial bucket is added after the weighted per-cycle component buckets and
# before sound-speed propagation. The T-S covariance term is intentionally zero:
# no cross term is included in the sound-speed variance.

# %%
if uncertainty_product_cache_valid:
    uncertainty_product = pd.read_pickle(uncertainty_product_path)
else:
    records = []
    for lat, lon in tqdm(lat_lon_product):
        records.extend(
            uncertainty_product_builder.query(latitude=lat, longitude=lon).to_dict("records")
        )

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


benchmark_cache_valid = benchmark_path.exists() and cache_metadata_matches(
    benchmark_metadata_path,
    benchmark_metadata,
)

if benchmark_cache_valid:
    benchmark_results = pd.read_csv(benchmark_path)
else:
    precompute_start = time.perf_counter()
    uncertainty_product_builder.precompute_cycle_terms()
    precompute_seconds = time.perf_counter() - precompute_start
    benchmark_results = pd.DataFrame(
        [
            run_benchmark_case(
                case,
                product_builder=uncertainty_product_builder,
                box=box,
                target_pressure=target_pressure,
                precompute_seconds=precompute_seconds,
            )
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
    box=box,
    title=chart_title("Bay of Bengal TEOS-10 Sound Speed at 110 m", analysis_date_label),
    cbar_label="Sound speed (m/s)",
    cmap=sound_speed_contour_cmap,
    interpolation=heatmap_interpolation,
    vmin=sound_speed_limits[0],
    vmax=sound_speed_limits[1],
)
chart_exports["sound_speed_teos10_110m"] = save_figure(
    fig, chart_path=chart_path, stem="sound_speed_teos10_110m"
)

fig, ax = plot_matrix(
    sigma_sound_speed_110m,
    box=box,
    title=chart_title("Bay of Bengal Sound-Speed Sigma at 110 m", analysis_date_label),
    cbar_label="Sigma (m/s)",
    cmap="magma",
    interpolation=heatmap_interpolation,
    vmin=sigma_limits[0],
    vmax=sigma_limits[1],
)
chart_exports["sigma_sound_speed_teos10_110m"] = save_figure(
    fig, chart_path=chart_path, stem="sigma_sound_speed_teos10_110m"
)

fig, ax = plot_support_matrix(
    support_raw_110m,
    box=box,
    title=chart_title("Bay of Bengal Raw Support Weight at 110 m", analysis_date_label),
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
chart_exports["w_raw_110m"] = save_figure(
    fig, chart_path=chart_path, stem="w_raw_110m"
)

fig, ax = plot_matrix_with_support_contours(
    sound_speed_110m,
    support_raw_110m,
    box=box,
    title=chart_title(
        "Bay of Bengal TEOS-10 Sound Speed at 110 m with Raw W Contours",
        analysis_date_label,
    ),
    cbar_label="Sound speed (m/s)",
    cmap=sound_speed_contour_cmap,
    interpolation=heatmap_interpolation,
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
    chart_path=chart_path,
    stem="sound_speed_teos10_w_contours_110m",
)

fig, ax = plot_matrix_with_support_contours(
    sigma_sound_speed_110m,
    support_raw_110m,
    box=box,
    title=chart_title(
        "Bay of Bengal Sound-Speed Sigma at 110 m with Raw W Contours",
        analysis_date_label,
    ),
    cbar_label="Sigma (m/s)",
    cmap="magma",
    interpolation=heatmap_interpolation,
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
    chart_path=chart_path,
    stem="sigma_sound_speed_teos10_w_contours_110m",
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
