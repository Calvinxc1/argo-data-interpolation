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
# # Jana-style hold-one-float-out validation
#
# This notebook turns the calibrated Jana et al. (2022) replication pipeline into an explicit held-out benchmark. The benchmark predictor deliberately stays close to the paper's spatial aggregation logic rather than reusing the weighted retained-cycle construction from `3-uncertainty-extension.ipynb`.
#
# It is the second notebook in the acoustics sequence. Notebook `1` settled the descriptive replication baseline; this notebook is the first predictive test built on that archive.
#
# The governing question here is narrow:
# - if one float is held out entirely
# - and the remaining retained archive is used as a flat Jana-style `2° x 2°` local retained-cycle kernel
# - how well does that simple baseline recover the held-out cycle profiles on the common depth grid?
#
# This notebook therefore evaluates a **Jana-style local-kernel baseline**. It is not intended to reproduce every figure in the replication notebook, and it is not intended to replace the more flexible weighted spatio-temporal reconstruction sketch.
#
# ## Benchmark scope
#
# The validation design is intentionally conservative:
# - hold out by `PLATFORM_NUMBER` to avoid same-float leakage
# - rebuild predictions on the retained `5-500 m` common depth grid
# - predict temperature and salinity by the unweighted retained-cycle mean inside a flat `2° x 2°` latitude-longitude kernel
# - compute predicted sound speed from predicted temperature and salinity using the held-out cycle pressure grid
# - aggregate RMSE, MAE, and bias by depth across all evaluated held-out cycles
#
# ## Deliberate simplifications
#
# To keep the benchmark interpretable, the notebook does **not**:
# - rerun the full archive-retention and outlier-screen process inside every held-out fold
# - impose Jana's monthly coverage rule from the gridded map figures on the retained-cycle set
# - use seasonal or interannual weights
# - use the package's profile-internal `n_folds` diagnostics as a substitute for cross-cycle validation
#
# The retained archive is frozen using the same calibrated replication assumptions as `1-jana-study-replication.ipynb`, especially the `3 SD` profile screen and the linear-interpolation baseline.
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
from argo_interp.cycle.model import Model
from argo_interp.cycle.domain import ModelData, ModelMeta
from argo_interp.cycle.config import ModelSettings, ModelKwargs

# %% [markdown]
# ## 1. Pull the Bay of Bengal Argo archive directly
#
# This notebook now performs its own Argo pull so it can be run independently of
# `1-jana-study-replication.ipynb`. The fetched domain matches the replication
# notebook so the retained archive is still comparable.
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
# ## 2. Rebuild the calibrated Jana retained archive
#
# The steps below intentionally mirror the settled replication assumptions:
# - keep only QC flags `1` and `2`
# - retain cycles that sample the upper `20 m` and extend to `500 m` or deeper
# - average duplicate pressure rows before fitting
# - use linear interpolation as the replication baseline
# - apply the calibrated `3 SD` whole-profile outlier screen after interpolation to the common depth grid
#
# The goal is to validate the **same retained archive** that supports the current replication notebook, not to define a stricter nested-CV protocol.
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

    if pressure.min() > gsw.p_from_z(-20, latitude):
        continue
    if pressure.max() < gsw.p_from_z(-500, latitude):
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
    })

pres_profiles = pd.concat(pres_profiles, axis=1)
temp_profiles = pd.concat(temp_profiles, axis=1)
sal_profiles = pd.concat(sal_profiles, axis=1)
cycle_metadata = pd.DataFrame.from_records(cycle_records).set_index("cycle_id")

# %%
temp_mean = pd.concat([
    temp_profiles.mean(axis=1).rename("mean"),
    temp_profiles.std(axis=1).rename("stdev"),
], axis=1)
sal_mean = pd.concat([
    sal_profiles.mean(axis=1).rename("mean"),
    sal_profiles.std(axis=1).rename("stdev"),
], axis=1)

temp_stdev = temp_mean["stdev"].replace(0, np.nan)
sal_stdev = sal_mean["stdev"].replace(0, np.nan)

temp_z_profiles = (temp_profiles - temp_mean["mean"].values[:, np.newaxis]) / temp_stdev.values[:, np.newaxis]
sal_z_profiles = (sal_profiles - sal_mean["mean"].values[:, np.newaxis]) / sal_stdev.values[:, np.newaxis]

sd_val = 3
temp_fail = (temp_z_profiles.abs() >= sd_val).any(axis=0)
sal_fail = (sal_z_profiles.abs() >= sd_val).any(axis=0)
active_cycles = temp_fail.index[~temp_fail & ~sal_fail]

pres_active_profiles = pres_profiles[active_cycles]
temp_active_profiles = temp_profiles[active_cycles]
sal_active_profiles = sal_profiles[active_cycles]
active_cycles_metadata = cycle_metadata.loc[active_cycles].copy()
sound_speed_profiles = pd.DataFrame(
    sw.svel(sal_active_profiles, temp_active_profiles, pres_active_profiles),
    index=temp_active_profiles.index,
    columns=temp_active_profiles.columns,
)

print(f"Retained active cycles: {len(active_cycles):,}")
print(f"Retained floats: {active_cycles_metadata['platform_number'].nunique():,}")

# %% [markdown]
# ## 3. Define the Jana-style hold-one-float-out predictor
#
# The predictor is intentionally simple:
# - exclude every cycle from the held-out float
# - keep retained cycles inside a flat `2° x 2°` kernel centered on the target cycle
# - average retained-cycle temperature and salinity profiles on the common depth grid
# - derive predicted sound speed from those predicted temperature and salinity profiles
#
# Cycles without enough retained-cycle support are skipped rather than imputed. The skip accounting matters because a flat local kernel is only meaningful where the retained archive is actually dense enough to support it.
#
# This is a deliberately conservative benchmark, not a claim that the flat kernel is the best predictor. It is defensible because it stays close to Jana et al.'s published spatial aggregation logic and therefore gives the later weighted notebooks a clear deterministic baseline to beat.
#
# The `min_cycles = 30` threshold is a local validation choice rather than a source-backed constant. It was chosen as a pragmatic support floor so the local mean is not driven by a handful of nearby cycles, and because it stays in the same rough minimum-support spirit as Jana's map-level coverage rules without pretending to reproduce them exactly.
#

# %%
@dataclass(frozen=True, slots=True)
class HoldoutConfig:
    kernel_half_width_deg: float = 1.0
    min_cycles: int = 30
    max_platforms: int | None = None
    random_seed: int = 42


config = HoldoutConfig()
config

# %%
def retained_cycle_ids(target_meta: pd.Series, cycle_metadata: pd.DataFrame, cfg: HoldoutConfig) -> pd.Index:
    lat_mask = (cycle_metadata["latitude"] - target_meta["latitude"]).abs() <= cfg.kernel_half_width_deg
    lon_mask = (cycle_metadata["longitude"] - target_meta["longitude"]).abs() <= cfg.kernel_half_width_deg
    return cycle_metadata.index[lat_mask & lon_mask]


def predict_cycle_jana_style(
    cycle_id: str,
    cycle_metadata: pd.DataFrame,
    temp_grid: pd.DataFrame,
    sal_grid: pd.DataFrame,
    pressure_grid: pd.DataFrame,
    cfg: HoldoutConfig,
) -> tuple[pd.DataFrame | None, dict]:
    target_meta = cycle_metadata.loc[cycle_id]
    cycle_metadata = cycle_metadata[cycle_metadata["platform_number"] != target_meta["platform_number"]]
    retained_ids = retained_cycle_ids(target_meta, cycle_metadata, cfg)

    diagnostics = {
        "cycle_id": cycle_id,
        "platform_number": target_meta["platform_number"],
        "retained_cycle_count": int(len(retained_ids)),
        "status": "ok",
    }

    if len(retained_ids) < cfg.min_cycles:
        diagnostics["status"] = "insufficient_cycles"
        return None, diagnostics

    predict_temp = temp_grid[retained_ids].mean(axis=1)
    predict_sal = sal_grid[retained_ids].mean(axis=1)
    predict_spd = pd.Series(
        sw.svel(predict_sal.values, predict_temp.values, pressure_grid[cycle_id].values),
        index=temp_grid.index,
        name="sound_speed",
    )

    predicts = pd.concat([
        predict_temp.rename("temperature"),
        predict_sal.rename("salinity"),
        predict_spd,
    ], axis=1)
    return predicts, diagnostics

# %%
rng = np.random.default_rng(config.random_seed)
platform_numbers = np.sort(active_cycles_metadata["platform_number"].unique())

if config.max_platforms is not None and config.max_platforms < len(platform_numbers):
    platform_numbers = np.sort(rng.choice(platform_numbers, size=config.max_platforms, replace=False))

print(f"Platforms scheduled for evaluation: {len(platform_numbers):,}")

# %% [markdown]
# ## 4. Run the hold-one-float-out evaluation
#
# This notebook evaluates directly from the rebuilt archive so its diagnostics and
# figures always reflect the current run rather than a saved result cache.
#

# %%
cycle_metrics_records = []
residuals_long_records = []
diagnostics_records = []
sample_profiles = {}

evaluated_cycles = active_cycles_metadata[active_cycles_metadata["platform_number"].isin(platform_numbers)].index
t = tqdm(evaluated_cycles, total=len(evaluated_cycles))
for cycle_id in t:
    predicts, diag = predict_cycle_jana_style(
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
        "temperature_rmse": np.sqrt((residuals["temperature"] ** 2).mean()),
        "temperature_mae": residuals["temperature"].abs().mean(),
        "temperature_bias": residuals["temperature"].mean(),
        "salinity_rmse": np.sqrt((residuals["salinity"] ** 2).mean()),
        "salinity_mae": residuals["salinity"].abs().mean(),
        "salinity_bias": residuals["salinity"].mean(),
        "sound_speed_rmse": np.sqrt((residuals["sound_speed"] ** 2).mean()),
        "sound_speed_mae": residuals["sound_speed"].abs().mean(),
        "sound_speed_bias": residuals["sound_speed"].mean(),
    })

    for measure in ["temperature", "salinity", "sound_speed"]:
        residuals_long_records.append(pd.DataFrame({
            "cycle_id": cycle_id,
            "platform_number": diag["platform_number"],
            "depth": residuals.index,
            "measure": measure,
            "residual": residuals[measure].values,
            "abs_error": residuals[measure].abs().values,
            "sq_error": residuals[measure].pow(2).values,
        }))

    if len(sample_profiles) < 4:
        sample_profiles[cycle_id] = {
            "predicts": predicts,
            "actuals": actuals,
            "diagnostics": diag,
        }

    t.set_postfix(evaluated=len(cycle_metrics_records), skipped=len(diagnostics_records) - len(cycle_metrics_records))

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
# ## 5. Coverage and retained-cycle-support diagnostics
#
# These summaries answer the first practical question: where can a Jana-style flat local kernel even be evaluated without collapsing for lack of nearby retained cycles?
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
    print(f"Retained-cycle count range: {cycle_metrics['retained_cycle_count'].min():.0f} to {cycle_metrics['retained_cycle_count'].max():.0f}")

# %%
fig, ax = plt.subplots(figsize=(8, 4))
cycle_metrics["retained_cycle_count"].hist(ax=ax, bins=30, color="#4c78a8", alpha=0.85)
ax.axvline(config.min_cycles, color="crimson", linestyle="--", linewidth=1.2, label="min_cycles")
ax.set_title("Held-out Jana benchmark retained-cycle counts")
ax.set_xlabel("Retained cycles inside flat 2° x 2° kernel")
ax.set_ylabel("Held-out cycles")
ax.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6. Aggregate benchmark performance by depth
#
# The plots below are the core benchmark output. They show how the simple Jana-style kernel behaves as a predictor, depth by depth, for temperature, salinity, and sound speed.
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
plt.suptitle("Jana-style hold-one-float-out error by depth")
plt.tight_layout()
plt.show()

# %%
cycle_metrics[[
    "temperature_rmse", "salinity_rmse", "sound_speed_rmse",
    "temperature_mae", "salinity_mae", "sound_speed_mae",
]].describe().T

# %% [markdown]
# ## 7. Spatial coverage of evaluated and skipped cycles
#
# The map below makes the skip pattern visible. A flat local kernel is only a useful baseline where the retained archive is dense enough to support it.
#

# %%
coverage_map = active_cycles_metadata.join(diagnostics[["status", "retained_cycle_count"]], how="left")

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
ax.scatter(
    coverage_map.loc[ok_mask, "longitude"],
    coverage_map.loc[ok_mask, "latitude"],
    s=6,
    c="#1f77b4",
    alpha=0.45,
    label="evaluated",
    transform=projection,
)
ax.scatter(
    coverage_map.loc[~ok_mask, "longitude"],
    coverage_map.loc[~ok_mask, "latitude"],
    s=8,
    c="crimson",
    alpha=0.6,
    label="skipped",
    transform=projection,
)
ax.legend(loc="upper right")
ax.set_title("Jana-style hold-one-float-out coverage")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 8. Example held-out profiles
#
# These examples are not meant to prove global skill. They are there to show how the benchmark behaves on individual cycles and whether the flat retained-cycle mean stays inside a coherent local profile family.
#

# %%
def plot_sample_profile(cycle_id: str) -> None:
    sample = sample_profiles[cycle_id]
    predicts = sample["predicts"]
    actuals = sample["actuals"]
    retained_cycle_count = sample["diagnostics"]["retained_cycle_count"]
    actual_color = "#444444"

    fig, axes = plt.subplots(1, 3, figsize=(12, 6), sharey=True)
    for ax, measure, color in zip(
        axes,
        ["temperature", "salinity", "sound_speed"],
        ["#1f77b4", "#2ca02c", "#d62728"],
    ):
        ax.plot(actuals[measure], actuals.index, label="actual", color=actual_color, linewidth=1.8)
        ax.plot(predicts[measure], predicts.index, label="predicted", color=color, linewidth=1.5)
        ax.set_title(measure_labels[measure])
        ax.set_xlabel(measure)
        ax.set_ylim(500, 0)
        ax.grid(True, linewidth=0.3, alpha=0.5)

    axes[0].set_ylabel("Depth (m)")
    axes[0].legend(loc="lower right")
    plt.suptitle(f"{cycle_id} | Jana-style holdout prediction | retained cycles={retained_cycle_count}")
    plt.tight_layout()
    plt.show()

# %%
for cycle_id in sample_profiles:
    plot_sample_profile(cycle_id)

# %% [markdown]
# ## 9. Interpretation and next step
#
# This notebook is designed to answer one specific baseline question: how far can a flat Jana-style local-kernel predictor go before more explicit spatio-temporal structure is needed?
#
# The benchmark is most useful if it stays narrow:
# - it validates the replication archive with a held-out task
# - it provides a simple baseline for later comparison against weighted retained-cycle or model-based approaches
# - it makes the coverage-versus-skill tradeoff visible through retained-cycle-count diagnostics and skip patterns
#
# The next notebook in the sequence, `3-uncertainty-extension.ipynb`, changes only one major thing: the predictor. It keeps the same strict retained archive and the same hold-one-float-out frame, but replaces the flat local mean with a weighted retained-cycle construction.
#
# That makes the comparison intentionally clean:
# - notebook `2` asks what the flat Jana-style kernel can do on its own
# - notebook `3` asks whether modest spatial, seasonal, and interannual weighting improves that same held-out task
#
# More exploratory variants, such as changing `min_cycles`, adding seasonal hard filters, or repeating the same benchmark with PCHIP, remain secondary until that baseline-versus-weighted comparison is clear.
