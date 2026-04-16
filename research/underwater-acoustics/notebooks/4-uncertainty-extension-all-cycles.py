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
#     display_name: Python 3
#     language: python
#     name: python3
#   language_info:
#     codemirror_mode:
#       name: ipython
#       version: 3
#     file_extension: .py
#     mimetype: text/x-python
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#     version: 3.14.3
# ---

# %% [markdown]
# # Relaxed-archive weighted local-window hold-one-float-out validation
#
# This notebook keeps the same hold-one-float-out validation frame used by `2-jana-holdout-validation.ipynb` and `3-uncertainty-extension.ipynb`, but it relaxes the archive-retention logic instead of removing the local moving window.
#
# It is the fourth notebook in the acoustics sequence. Notebook `3` tested whether weighting helps under the strict retained archive; this notebook tests whether the same weighted local-window idea benefits from a less aggressively pruned local archive.
#
# In this version:
# - the held-out float is still excluded completely
# - nearby retained cycles are still selected with a flat local moving window
# - cycles are not dropped for failing the upper-`20 m` or lower-`500 m` coverage requirements
# - profiles are scored only over the held-out cycle's actual sampled depth range
# - depths with no local supporting cycles are dropped and counted explicitly
#
# The goal is to test whether the weighted local-window approach improves when the archive is allowed to retain more partially sampled cycles.
#
# ## Comparison target
#
# This notebook should be read alongside the other three:
# - `1-jana-study-replication`: strict replication archive and descriptive outputs
# - `2-jana-holdout-validation`: strict retained archive with a flat local mean
# - `3-uncertainty-extension`: strict retained archive with a weighted local mean
# - `4-uncertainty-extension-all-cycles`: relaxed retained archive with the same weighted local window
#
# That makes the progression explicit:
# - replication
# - strict local benchmark
# - strict weighted local extension
# - relaxed-archive weighted local extension
#

# %%
from dataclasses import dataclass
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import gsw
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seawater as sw
from tqdm.auto import tqdm

# %%
from argo_interp.data import data_filter, get_data
from argo_interp.cycle.adapter import LinearAdapter
from argo_interp.cycle.config import ModelKwargs, ModelSettings
from argo_interp.cycle.domain import ModelData, ModelMeta
from argo_interp.cycle.model import Model

# %% [markdown]
# ## 1. Pull the Bay of Bengal Argo archive directly
#
# This notebook now performs its own Argo pull so it can be run independently of
# the earlier notebooks while preserving the same spatial-temporal source box.
#

# %%
notebook_dir = Path(".")
data_path = notebook_dir / "data"
chart_path = data_path / "charts"
chart_path.mkdir(exist_ok=True, parents=True)

box = [
    80, 99,
    6, 23,
    0, 750,
    "2011-01-01", "2020-12-31",
]
ds = get_data(box, progress=True)

# %% [markdown]
# ## 2. Build a relaxed weighted-validation archive
#
# This notebook still keeps QC filtering and duplicate-pressure cleanup, but it deliberately relaxes the stricter retained-archive rules:
# - QC flags `1` and `2` only
# - no required upper-`20 m` sampling
# - no required extension to `500 m`
# - no whole-profile outlier exclusion
# - linear interpolation to the common depth grid, with values masked outside each profile's actual sampled pressure range
#
# That masking step matters. It keeps partially sampled profiles in the archive without pretending they contain information above or below their actual sampled depth range.
#

# %%
ds_filters = [
    ds["PRES_QC"].isin([1, 2]),
    ds["TEMP_QC"].isin([1, 2]),
    ds["PSAL_QC"].isin([1, 2]),
]
ds = data_filter(ds, ds_filters)

settings = ModelSettings(
    n_folds=2,
    model_kwargs=ModelKwargs(
        temperature=dict(extrapolate=True),
        salinity=dict(extrapolate=True),
    ),
)

models = {}

cycles = len(ds[["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"]].to_dataframe().drop_duplicates())
t = tqdm(ds.groupby(["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"]), total=cycles)
for (platform_number, cycle_number, direction), cycle_ds in t:
    pressure = cycle_ds["PRES"].values
    temperature = cycle_ds["TEMP"].values
    salinity = cycle_ds["PSAL"].values

    latitude = cycle_ds["LATITUDE"].values[0]
    longitude = cycle_ds["LONGITUDE"].values[0]
    timestamp = cycle_ds["TIME"].values[0]

    if cycle_ds.sizes["N_POINTS"] < 2:
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
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
        profile_pressure=(pressure.min(), pressure.max()),
    )
    cycle_id = model_meta.cycle_id

    linear_model = Model.build(model_meta, model_data, LinearAdapter, settings)
    models[cycle_id] = linear_model
    t.set_postfix(model_count=len(models))

# %%
depth_grid = pd.Index(np.arange(5, 501, 1), name="depth")

pres_profiles = []
temp_profiles = []
sal_profiles = []
cycle_records = []

for cycle_id, model in tqdm(models.items()):
    pressure_grid = pd.Series(gsw.p_from_z(-depth_grid, model.meta.latitude), index=depth_grid, name=cycle_id)
    interp = model.interpolate(pressure_grid).to_frame().set_index(pressure_grid.index)

    # Mask values outside the profile's actual sampled pressure range.
    profile_min, profile_max = model.meta.profile_pressure
    supported = (pressure_grid >= profile_min) & (pressure_grid <= profile_max)
    interp.loc[~supported, ["temperature", "salinity"]] = np.nan

    pres_profiles.append(pressure_grid)
    temp_profiles.append(interp["temperature"].rename(cycle_id))
    sal_profiles.append(interp["salinity"].rename(cycle_id))
    cycle_records.append({
        "cycle_id": cycle_id,
        "platform_number": model.meta.platform_number,
        "cycle_number": model.meta.cycle_number,
        "direction": model.meta.direction,
        "latitude": model.meta.latitude,
        "longitude": model.meta.longitude,
        "timestamp": model.meta.timestamp,
        "min_pressure": profile_min,
        "max_pressure": profile_max,
    })

pres_profiles = pd.concat(pres_profiles, axis=1)
temp_profiles = pd.concat(temp_profiles, axis=1)
sal_profiles = pd.concat(sal_profiles, axis=1)
cycle_metadata = pd.DataFrame.from_records(cycle_records).set_index("cycle_id")

active_cycles = cycle_metadata.index
pres_active_profiles = pres_profiles[active_cycles]
temp_active_profiles = temp_profiles[active_cycles]
sal_active_profiles = sal_profiles[active_cycles]
active_cycles_metadata = cycle_metadata.loc[active_cycles].copy()
sound_speed_profiles = pd.DataFrame(
    sw.svel(sal_active_profiles, temp_active_profiles, pres_active_profiles),
    index=temp_active_profiles.index,
    columns=temp_active_profiles.columns,
)

print(f"Retained cycles after relaxed archive build: {len(active_cycles):,}")
print(f"Retained floats after relaxed archive build: {active_cycles_metadata['platform_number'].nunique():,}")

# %% [markdown]
# ## 3. Define the weighted local-window predictor
#
# The local moving window is preserved. For each held-out cycle:
# - only nearby cycles inside a flat `2° x 2°` window can contribute
# - nearby cycles are weighted by distance, seasonal alignment, and interannual proximity
# - the prediction is formed depth by depth using only locally available support
#
# If the held-out cycle has sampled a depth where none of the nearby cycles provide support, that depth is dropped from scoring and counted explicitly.
#
# As in notebook `3`, the weighting function uses only the exponential numerator of a Gaussian-style kernel. The omitted normalizing constant would be wasted computation here because the weights are used only relatively and are renormalized by the weighted-average step; it would not change which cycles get emphasized when each component uses a fixed variance term.
#
# The bandwidth choices in `HoldoutConfig` are still heuristic. They are reasonable starting values for a local spatio-temporal taper, but they are not evidence-backed defaults and should be read as transparent modeling choices rather than settled parameter estimates.
#
# This notebook changes one additional design choice: `min_cycles = 1`. That is acceptable here only because the relaxed-archive experiment is explicitly about depthwise local support. The goal is not to claim that a single supporting cycle is a stable prediction, but to expose where partial profiles provide some support, where they provide none, and how many held-out depths still have to be dropped.
#
# A full sensitivity analysis over kernel width, support thresholds, and temporal bandwidths remains future work. Because the holdout pass is computationally expensive, that analysis should be planned as a targeted experiment rather than a broad brute-force sweep.
#

# %%
@dataclass(frozen=True, slots=True)
class HoldoutConfig:
    kernel_half_width_deg: float = 1.0
    min_cycles: int = 1
    seasonal_window_weeks: int = 8
    dist_stdev_cutoff: float = 3.0
    week_stdev_cutoff: float = 3.0
    annual_stdev_years: float = 2.0
    max_platforms: int | None = None
    random_seed: int = 42
    plot_top_cycles: int = 40


config = HoldoutConfig()
config

# %%
def calc_weight(x2: pd.Series | np.ndarray | float, var: float) -> pd.Series | np.ndarray | float:
    return np.exp(-x2 / (2 * var))


def effective_cycle_count(weights: pd.Series) -> float:
    return float((weights.sum() ** 2) / weights.pow(2).sum())


def retained_cycle_ids(target_meta: pd.Series, cycle_metadata: pd.DataFrame, cfg: HoldoutConfig) -> pd.Index:
    lat_mask = (cycle_metadata["latitude"] - target_meta["latitude"]).abs() <= cfg.kernel_half_width_deg
    lon_mask = (cycle_metadata["longitude"] - target_meta["longitude"]).abs() <= cfg.kernel_half_width_deg
    return cycle_metadata.index[lat_mask & lon_mask]


def retained_cycle_weights(target_meta: pd.Series, local_cycle_metadata: pd.DataFrame, cfg: HoldoutConfig) -> pd.Series:
    dist_sq = (
        (local_cycle_metadata[["latitude", "longitude"]] - target_meta[["latitude", "longitude"]].astype(float)) ** 2
    ).sum(axis=1)
    dist_stdev = cfg.kernel_half_width_deg / cfg.dist_stdev_cutoff
    dist_weight = calc_weight(dist_sq, dist_stdev ** 2)

    seconds_in_week = 60 * 60 * 24 * 7
    seasonal_sq = (
        local_cycle_metadata["timestamp"].apply(lambda x: x.replace(year=2000))
        - target_meta["timestamp"].replace(year=2000)
    ).dt.total_seconds() ** 2
    seasonal_stdev = (cfg.seasonal_window_weeks / 2) / cfg.week_stdev_cutoff * seconds_in_week
    seasonal_weight = calc_weight(seasonal_sq, seasonal_stdev ** 2)

    seconds_in_year = 60 * 60 * 24 * 365.25
    annual_sq = (local_cycle_metadata["timestamp"] - target_meta["timestamp"]).dt.total_seconds() ** 2
    annual_stdev = cfg.annual_stdev_years * seconds_in_year
    annual_weight = calc_weight(annual_sq, annual_stdev ** 2)

    weights = dist_weight * seasonal_weight * annual_weight
    weights = weights / weights.max()
    return weights.rename("weight")


def predict_cycle_relaxed_archive(
    cycle_id: str,
    cycle_metadata: pd.DataFrame,
    temp_grid: pd.DataFrame,
    sal_grid: pd.DataFrame,
    pressure_grid: pd.DataFrame,
    cfg: HoldoutConfig,
) -> tuple[pd.DataFrame | None, dict, pd.Series | None]:
    target_meta = cycle_metadata.loc[cycle_id]
    candidate_metadata = cycle_metadata[cycle_metadata["platform_number"] != target_meta["platform_number"]]
    retained_ids = retained_cycle_ids(target_meta, candidate_metadata, cfg)

    diagnostics = {
        "cycle_id": cycle_id,
        "platform_number": target_meta["platform_number"],
        "retained_cycle_count": int(len(retained_ids)),
        "effective_cycle_count": np.nan,
        "target_depth_count": int(temp_grid[cycle_id].notna().sum()),
        "scored_depth_count": 0,
        "dropped_depth_count": 0,
        "status": "ok",
    }

    if len(retained_ids) < cfg.min_cycles:
        diagnostics["status"] = "insufficient_cycles"
        diagnostics["dropped_depth_count"] = diagnostics["target_depth_count"]
        return None, diagnostics, None

    local_metadata = candidate_metadata.loc[retained_ids]
    weights = retained_cycle_weights(target_meta, local_metadata, cfg)
    diagnostics["effective_cycle_count"] = effective_cycle_count(weights)

    temp_weight = temp_grid[retained_ids].notnull().mul(weights, axis=1)
    sal_weight = sal_grid[retained_ids].notnull().mul(weights, axis=1)
    temp_weight_sum = temp_weight.sum(axis=1)
    sal_weight_sum = sal_weight.sum(axis=1)

    predict_temp = pd.Series(np.nan, index=temp_grid.index, name="temperature")
    predict_sal = pd.Series(np.nan, index=sal_grid.index, name="salinity")

    temp_supported = temp_weight_sum > 0
    sal_supported = sal_weight_sum > 0
    predict_temp.loc[temp_supported] = (
        (temp_grid[retained_ids] * temp_weight).sum(axis=1).loc[temp_supported] / temp_weight_sum.loc[temp_supported]
    )
    predict_sal.loc[sal_supported] = (
        (sal_grid[retained_ids] * sal_weight).sum(axis=1).loc[sal_supported] / sal_weight_sum.loc[sal_supported]
    )

    predict_spd = pd.Series(
        sw.svel(predict_sal.values, predict_temp.values, pressure_grid[cycle_id].values),
        index=temp_grid.index,
        name="sound_speed",
    )

    predicts = pd.concat([
        predict_temp,
        predict_sal,
        predict_spd,
    ], axis=1)

    target_supported = temp_grid[cycle_id].notna() & sal_grid[cycle_id].notna()
    predicted_supported = predict_temp.notna() & predict_sal.notna()
    diagnostics["scored_depth_count"] = int((target_supported & predicted_supported).sum())
    diagnostics["dropped_depth_count"] = int((target_supported & ~predicted_supported).sum())

    if diagnostics["scored_depth_count"] == 0:
        diagnostics["status"] = "unsupported_depths"
        return None, diagnostics, weights

    return predicts, diagnostics, weights

# %%
rng = np.random.default_rng(config.random_seed)
platform_numbers = np.sort(active_cycles_metadata["platform_number"].unique())

if config.max_platforms is not None and config.max_platforms < len(platform_numbers):
    platform_numbers = np.sort(rng.choice(platform_numbers, size=config.max_platforms, replace=False))

print(f"Platforms scheduled for evaluation: {len(platform_numbers):,}")

# %% [markdown]
# ## 4. Run the relaxed-archive hold-one-float-out evaluation
#
# This notebook evaluates directly from the rebuilt relaxed archive. The key
# diagnostic remains the number of held-out depths dropped because no nearby
# cycle can support them.
#

# %%
cycle_metrics_records = []
residuals_long_records = []
diagnostics_records = []
sample_profiles = {}

evaluated_cycles = active_cycles_metadata[active_cycles_metadata["platform_number"].isin(platform_numbers)].index
t = tqdm(evaluated_cycles, total=len(evaluated_cycles))
for cycle_id in t:
    predicts, diag, weights = predict_cycle_relaxed_archive(
        cycle_id=cycle_id,
        cycle_metadata=active_cycles_metadata,
        temp_grid=temp_active_profiles,
        sal_grid=sal_active_profiles,
        pressure_grid=pres_active_profiles,
        cfg=config,
    )
    diagnostics_records.append(diag)

    if predicts is None:
        continue

    actuals = pd.concat([
        temp_active_profiles[cycle_id].rename("temperature"),
        sal_active_profiles[cycle_id].rename("salinity"),
        sound_speed_profiles[cycle_id].rename("sound_speed"),
    ], axis=1)

    residuals = predicts - actuals
    cycle_metrics_records.append({
        "cycle_id": cycle_id,
        "platform_number": diag["platform_number"],
        "retained_cycle_count": diag["retained_cycle_count"],
        "effective_cycle_count": diag["effective_cycle_count"],
        "target_depth_count": diag["target_depth_count"],
        "scored_depth_count": diag["scored_depth_count"],
        "dropped_depth_count": diag["dropped_depth_count"],
        "temperature_rmse": np.sqrt(np.nanmean(residuals["temperature"] ** 2)),
        "temperature_mae": residuals["temperature"].abs().mean(),
        "temperature_bias": residuals["temperature"].mean(),
        "salinity_rmse": np.sqrt(np.nanmean(residuals["salinity"] ** 2)),
        "salinity_mae": residuals["salinity"].abs().mean(),
        "salinity_bias": residuals["salinity"].mean(),
        "sound_speed_rmse": np.sqrt(np.nanmean(residuals["sound_speed"] ** 2)),
        "sound_speed_mae": residuals["sound_speed"].abs().mean(),
        "sound_speed_bias": residuals["sound_speed"].mean(),
    })

    for measure in ["temperature", "salinity", "sound_speed"]:
        measure_residuals = residuals[measure].dropna()
        residuals_long_records.append(pd.DataFrame({
            "cycle_id": cycle_id,
            "platform_number": diag["platform_number"],
            "depth": measure_residuals.index,
            "measure": measure,
            "residual": measure_residuals.values,
            "abs_error": measure_residuals.abs().values,
            "sq_error": measure_residuals.pow(2).values,
        }))

    if len(sample_profiles) < 4:
        sample_profiles[cycle_id] = {
            "predicts": predicts,
            "actuals": actuals,
            "diagnostics": diag,
            "weights": weights,
        }

    t.set_postfix(
        evaluated=len(cycle_metrics_records),
        dropped_depths=sum(record["dropped_depth_count"] for record in cycle_metrics_records),
    )

cycle_metrics = pd.DataFrame.from_records(cycle_metrics_records).set_index("cycle_id")
diagnostics = pd.DataFrame.from_records(diagnostics_records).set_index("cycle_id")
residuals_long = pd.concat(residuals_long_records, axis=0, ignore_index=True)

depth_metrics = residuals_long.groupby(["measure", "depth"]).agg(
    bias=("residual", "mean"),
    mae=("abs_error", "mean"),
    rmse=("sq_error", lambda x: np.sqrt(np.mean(x))),
    n_cycles=("cycle_id", "nunique"),
).reset_index()

# %% [markdown]
# ## 5. Local-support and dropped-depth diagnostics
#
# The main new diagnostic here is not just whether a cycle can be evaluated. It is how many of the held-out cycle's sampled depths have to be dropped because the nearby archive provides no support there.
#

# %%
status_counts = diagnostics["status"].value_counts().rename_axis("status").to_frame("n_cycles")
status_counts["share"] = status_counts["n_cycles"] / status_counts["n_cycles"].sum()
status_counts

# %%
if not cycle_metrics.empty:
    print(f"Evaluated cycles: {len(cycle_metrics):,}")
    print(f"Skipped cycles: {(diagnostics['status'] != 'ok').sum():,}")
    print(f"Median retained-cycle count: {cycle_metrics['retained_cycle_count'].median():.0f}")
    print(f"Median effective cycle count: {cycle_metrics['effective_cycle_count'].median():.1f}")
    print(f"Median target depth count: {cycle_metrics['target_depth_count'].median():.0f}")
    print(f"Median scored depth count: {cycle_metrics['scored_depth_count'].median():.0f}")
    print(f"Median dropped depth count: {cycle_metrics['dropped_depth_count'].median():.0f}")
    print(f"Total dropped depths: {cycle_metrics['dropped_depth_count'].sum():,}")

# %%
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

cycle_metrics["retained_cycle_count"].hist(ax=axes[0], bins=30, color="#4c78a8", alpha=0.85)
axes[0].axvline(config.min_cycles, color="crimson", linestyle="--", linewidth=1.2, label="min_cycles")
axes[0].set_title("Relaxed-archive retained-cycle counts")
axes[0].set_xlabel("Retained cycles inside flat 2° x 2° kernel")
axes[0].set_ylabel("Held-out cycles")
axes[0].legend()

cycle_metrics["dropped_depth_count"].hist(ax=axes[1], bins=30, color="#f58518", alpha=0.85)
axes[1].set_title("Dropped held-out depths per cycle")
axes[1].set_xlabel("Held-out depths dropped for lack of local support")
axes[1].set_ylabel("Held-out cycles")

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6. Aggregate relaxed-archive performance by depth
#
# The plot layout matches the other validation notebooks so the relaxed-archive weighted local-window model can be compared directly against the stricter local-kernel versions.
#

# %%
measure_order = ["temperature", "salinity", "sound_speed"]
measure_labels = {
    "temperature": "Temperature",
    "salinity": "Salinity",
    "sound_speed": "Sound Speed",
}

fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharey=True)
for col, measure in enumerate(measure_order):
    measure_depth = depth_metrics[depth_metrics["measure"] == measure]
    metric_ax = axes[0, col]
    bias_ax = axes[1, col]

    metric_ax.plot(measure_depth["rmse"], measure_depth["depth"], label="RMSE", color="#1f77b4")
    metric_ax.plot(measure_depth["mae"], measure_depth["depth"], label="MAE", color="#ff7f0e")
    metric_ax.set_title(measure_labels[measure])
    metric_ax.set_xlabel("RMSE / MAE")
    metric_ax.set_ylim(500, 0)
    metric_ax.grid(True, linewidth=0.3, alpha=0.5)

    bias_ax.plot(measure_depth["bias"], measure_depth["depth"], label="Bias", color="#2ca02c")
    bias_ax.axvline(0, color="black", linewidth=0.6, alpha=0.5)
    bias_ax.set_xlabel("Bias")
    bias_ax.set_ylim(500, 0)
    bias_ax.grid(True, linewidth=0.3, alpha=0.5)

axes[0, 0].set_ylabel("Depth (m)")
axes[1, 0].set_ylabel("Depth (m)")
axes[0, 0].legend(loc="lower right")
axes[1, 0].legend(loc="lower right")
plt.suptitle("Relaxed-archive weighted hold-one-float-out error by depth")
plt.tight_layout()
plt.show()

# %%
cycle_metrics[[
    "temperature_rmse", "salinity_rmse", "sound_speed_rmse",
    "temperature_mae", "salinity_mae", "sound_speed_mae",
]].describe().T

# %% [markdown]
# ## 7. Spatial pattern of dropped depths
#
# The coverage map now emphasizes where local support is depth-limited rather than simply absent.
#

# %%
coverage_map = active_cycles_metadata.join(
    diagnostics[["status", "effective_cycle_count", "dropped_depth_count"]],
    how="left",
)

projection = ccrs.PlateCarree()
fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={"projection": projection})
ax.set_facecolor("lightblue")
ax.add_feature(cfeature.LAND, facecolor="lightgrey")
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.3)
ax.set_extent([79, 100, 5, 24], crs=projection)

gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="grey", alpha=0.5)
gl.top_labels = False
gl.right_labels = False

ok_mask = coverage_map["status"] == "ok"
sc = ax.scatter(
    coverage_map.loc[ok_mask, "longitude"],
    coverage_map.loc[ok_mask, "latitude"],
    s=10,
    c=coverage_map.loc[ok_mask, "dropped_depth_count"],
    cmap="magma_r",
    alpha=0.75,
    transform=projection,
)

if (~ok_mask).any():
    ax.scatter(
        coverage_map.loc[~ok_mask, "longitude"],
        coverage_map.loc[~ok_mask, "latitude"],
        s=12,
        c="crimson",
        alpha=0.7,
        label="skipped",
        transform=projection,
    )
    ax.legend(loc="upper right")

cb = plt.colorbar(sc, ax=ax, shrink=0.8, pad=0.03)
cb.set_label("Dropped held-out depths")
ax.set_title("Relaxed-archive dropped-depth map")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 8. Example held-out profiles
#
# The profile clouds below show the highest-weight local cycles that supported each held-out prediction. Depths with no local support appear as gaps in the predicted profile and contribute to the dropped-depth counts reported above.
#

# %%
def plot_sample_profile(cycle_id: str) -> None:
    sample = sample_profiles[cycle_id]
    predicts = sample["predicts"]
    actuals = sample["actuals"]
    retained_cycle_count = sample["diagnostics"]["retained_cycle_count"]
    effective_count = sample["diagnostics"]["effective_cycle_count"]
    dropped_depth_count = sample["diagnostics"]["dropped_depth_count"]
    weights = sample["weights"].sort_values(ascending=False)
    plot_weights = weights.head(config.plot_top_cycles)
    actual_color = "#444444"

    fig, axes = plt.subplots(1, 3, figsize=(12, 6), sharey=True)
    for ax, measure, color in zip(
        axes,
        ["temperature", "salinity", "sound_speed"],
        ["#1f77b4", "#2ca02c", "#d62728"],
    ):
        if measure in {"temperature", "salinity"}:
            profile_grid = temp_active_profiles if measure == "temperature" else sal_active_profiles
            for retained_cycle_id, weight in plot_weights.items():
                ax.plot(
                    profile_grid[retained_cycle_id],
                    profile_grid.index,
                    color=color,
                    alpha=float(0.05 + 0.25 * weight),
                    linewidth=0.5,
                )
        else:
            for retained_cycle_id, weight in plot_weights.items():
                ax.plot(
                    sound_speed_profiles[retained_cycle_id],
                    sound_speed_profiles.index,
                    color=color,
                    alpha=float(0.05 + 0.25 * weight),
                    linewidth=0.5,
                )

        ax.plot(actuals[measure], actuals.index, label="actual", color=actual_color, linewidth=1.8)
        ax.plot(predicts[measure], predicts.index, label="predicted", color=color, linewidth=1.5)
        ax.set_title(measure_labels[measure])
        ax.set_xlabel(measure)
        ax.set_ylim(500, 0)
        ax.grid(True, linewidth=0.3, alpha=0.5)

    axes[0].set_ylabel("Depth (m)")
    axes[0].legend(loc="lower right")
    plt.suptitle(
        f"{cycle_id} | Relaxed archive local weighted holdout | "
        f"retained cycles={retained_cycle_count} | "
        f"effective cycles={effective_count:.1f} | "
        f"dropped depths={dropped_depth_count}"
    )
    plt.tight_layout()
    plt.show()



# %%
for cycle_id in sample_profiles:
    plot_sample_profile(cycle_id)

# %% [markdown]
# ## 9. Interpretation and next step
#
# This notebook isolates a different question than the earlier `all cycles` idea:
#
# If the local moving window is preserved, how much does strict archive pruning matter once partially sampled profiles are allowed to contribute where they actually provide support?
#
# The key comparisons are:
# - strict weighted local window versus relaxed weighted local window skill by depth
# - whether thermocline errors improve when partial profiles are retained locally
# - whether dropped-depth counts reveal where local support still collapses despite the relaxed archive
#
# Read as a sequence, the four notebooks now separate the main questions cleanly:
# - notebook `1`: can the Jana workflow be replicated transparently enough to serve as a baseline?
# - notebook `2`: how strong is the flat Jana-style kernel as a held-out predictor?
# - notebook `3`: does weighted local aggregation beat that flat benchmark under the same strict archive?
# - notebook `4`: does the weighted approach improve further when partial local support is allowed back into the archive?
