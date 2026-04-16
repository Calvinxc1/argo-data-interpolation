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
# # Uncertainty model build handoff
#
# This notebook promotes the relaxed weighted local-window predictor from
# `4-uncertainty-extension-all-cycles.ipynb` into an explicit model-build stage.
# The intent is to stop at the deterministic model boundary so later notebooks can
# add uncertainty passthrough mechanics without having to rebuild or reinterpret
# the local archive each time.
#
# In scope here:
# - rebuild the relaxed weighted local-window archive used in notebook `4` when
#   no local model cache is present
# - confirm the deterministic backbone against the existing hold-one-float-out
#   validation frame
# - package the tables and sample local contexts needed for later uncertainty work
#
# Intentionally out of scope:
# - attaching sensor, equation, or interpolation uncertainty terms
# - propagating covariance, intervals, or ensembles through the local window
# - claiming a calibrated uncertainty representation before that later step exists
#
# ## Sequence position
#
# Read this as notebook `5` in the acoustics sequence:
# - `1-jana-study-replication`: deterministic Jana replication baseline
# - `2-jana-holdout-validation`: strict flat local benchmark
# - `3-uncertainty-extension`: strict weighted local extension
# - `4-uncertainty-extension-all-cycles`: relaxed weighted local extension
# - `5-uncertainty-model-build`: deterministic model-build handoff for later
#   uncertainty passthrough work

# %%
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path

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
# ## 1. Load the local model cache or rebuild from raw Argo data
#
# This notebook remains independent of notebooks `1` through `4`, but it now keeps
# its own deterministic model cache under `data/uncertainty_model_build.pkl`.
#
# If that cache exists and `override = False`, the notebook loads the saved model
# tables directly and skips the expensive source-data pull and rebuild path. If the
# cache is missing or `override = True`, the notebook performs its own Argo pull,
# rebuilds the model from raw inputs, validates it, and refreshes the cache.

# %%
notebook_dir = Path(".")
data_path = notebook_dir / "data"
chart_path = data_path / "charts"
chart_path.mkdir(exist_ok=True, parents=True)

model_cache_file = data_path / "uncertainty_model_build.pkl"
override = False
cached_model_build_artifact = None

if model_cache_file.exists() and not override:
    with model_cache_file.open("br") as f:
        cached_model_build_artifact = pickle.load(f)
    print(f"Loaded deterministic model-build cache from: {model_cache_file}")

# %% [markdown]
# ## 2. Rebuild the relaxed weighted local archive when needed
#
# This uses the same archive policy chosen in notebook `4`:
# - QC flags `1` and `2` only
# - retain partially sampled cycles
# - mask temperature and salinity outside each cycle's actual sampled pressure span
# - keep the common `5-500 m` depth grid for direct comparison against the earlier
#   validation notebooks

# %%
if cached_model_build_artifact is None:
    box = [
        80, 99,
        6, 23,
        0, 750,
        "2011-01-01", "2020-12-31",
    ]
    ds = get_data(box, progress=True)

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

    depth_grid = pd.Index(np.arange(5, 501, 1), name="depth")

    pres_profiles = []
    temp_profiles = []
    sal_profiles = []
    cycle_records = []

    for cycle_id, model in tqdm(models.items()):
        pressure_grid = pd.Series(gsw.p_from_z(-depth_grid, model.meta.latitude), index=depth_grid, name=cycle_id)
        interp = model.interpolate(pressure_grid).to_frame().set_index(pressure_grid.index)

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
# ## 3. Define the deterministic local-window model
#
# The local window remains the notebook `4` design choice:
# - flat `2° x 2°` candidate-retention kernel
# - weighted combination by distance, seasonal alignment, and interannual proximity
# - depthwise support masking, so partially sampled local cycles help only where they
#   actually provide information
#
# The new part in notebook `5` is the explicit local-context builder. That context is
# what later uncertainty passthrough code will need: target metadata, local retained
# cycles, depthwise support, and the local weighted deterministic prediction state.

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


if cached_model_build_artifact is None:
    config = HoldoutConfig()
else:
    config = HoldoutConfig(**cached_model_build_artifact["config"])
    depth_grid = pd.Index(cached_model_build_artifact["depth_grid"], name="depth")
    active_cycles_metadata = cached_model_build_artifact["cycle_metadata"]
    temp_active_profiles = cached_model_build_artifact["temperature_profiles"]
    sal_active_profiles = cached_model_build_artifact["salinity_profiles"]
    pres_active_profiles = cached_model_build_artifact["pressure_profiles"]
    sound_speed_profiles = cached_model_build_artifact["sound_speed_profiles"]
    cycle_metrics = cached_model_build_artifact["validation_cycle_metrics"]
    depth_metrics = cached_model_build_artifact["validation_depth_metrics"]
    diagnostics = cached_model_build_artifact["validation_diagnostics"]
    validation_summary = cached_model_build_artifact["validation_summary"]
    integrity_checks = cached_model_build_artifact["integrity_checks"]
    sample_contexts = cached_model_build_artifact["sample_contexts"]
    active_cycles = active_cycles_metadata.index
    print(f"Cached retained cycles: {len(active_cycles):,}")
    print(f"Cached retained floats: {active_cycles_metadata['platform_number'].nunique():,}")

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


def build_cycle_context(
    cycle_id: str,
    cycle_metadata: pd.DataFrame,
    temp_grid: pd.DataFrame,
    sal_grid: pd.DataFrame,
    pressure_grid: pd.DataFrame,
    sound_speed_grid: pd.DataFrame,
    cfg: HoldoutConfig,
) -> tuple[dict | None, dict]:
    target_meta = cycle_metadata.loc[cycle_id]
    candidate_metadata = cycle_metadata[cycle_metadata["platform_number"] != target_meta["platform_number"]]
    retained_ids = retained_cycle_ids(target_meta, candidate_metadata, cfg)

    diagnostics = {
        "cycle_id": cycle_id,
        "platform_number": target_meta["platform_number"],
        "retained_cycle_count": int(len(retained_ids)),
        "effective_cycle_count": np.nan,
        "target_depth_count": int((temp_grid[cycle_id].notna() & sal_grid[cycle_id].notna()).sum()),
        "scored_depth_count": 0,
        "dropped_depth_count": 0,
        "status": "ok",
    }

    if len(retained_ids) < cfg.min_cycles:
        diagnostics["status"] = "insufficient_cycles"
        diagnostics["dropped_depth_count"] = diagnostics["target_depth_count"]
        return None, diagnostics

    local_metadata = candidate_metadata.loc[retained_ids].copy()
    weights = retained_cycle_weights(target_meta, local_metadata, cfg)
    diagnostics["effective_cycle_count"] = effective_cycle_count(weights)

    temperature_local = temp_grid[retained_ids].copy()
    salinity_local = sal_grid[retained_ids].copy()
    pressure_local = pressure_grid[retained_ids].copy()
    sound_speed_local = sound_speed_grid[retained_ids].copy()
    target_pressure = pressure_grid[cycle_id].rename("pressure")

    support_mask = temperature_local.notna() & salinity_local.notna()
    support_weight = support_mask.mul(weights, axis=1)
    support_weight_sq = support_mask.mul(weights.pow(2), axis=1)

    weight_sum = support_weight.sum(axis=1).rename("weight_sum")
    depthwise_effective = (support_weight.sum(axis=1).pow(2) / support_weight_sq.sum(axis=1)).rename(
        "effective_cycle_count"
    )
    depthwise_effective = depthwise_effective.where(support_weight_sq.sum(axis=1) > 0)

    context = {
        "cycle_id": cycle_id,
        "target_meta": target_meta,
        "local_metadata": local_metadata,
        "weights": weights,
        "temperature_local": temperature_local,
        "salinity_local": salinity_local,
        "pressure_local": pressure_local,
        "sound_speed_local": sound_speed_local,
        "target_pressure": target_pressure,
        "support_mask": support_mask,
        "weight_sum": weight_sum,
        "depthwise_effective_cycle_count": depthwise_effective,
    }
    return context, diagnostics


def predict_cycle_from_context(context: dict) -> tuple[pd.DataFrame | None, dict]:
    temperature_local = context["temperature_local"]
    salinity_local = context["salinity_local"]
    weights = context["weights"]
    target_pressure = context["target_pressure"]
    support_mask = context["support_mask"]

    support_weight = support_mask.mul(weights, axis=1)
    weight_sum = support_weight.sum(axis=1)

    predict_temp = pd.Series(np.nan, index=temperature_local.index, name="temperature")
    predict_sal = pd.Series(np.nan, index=salinity_local.index, name="salinity")

    supported = weight_sum > 0
    predict_temp.loc[supported] = (
        (temperature_local * support_weight).sum(axis=1).loc[supported] / weight_sum.loc[supported]
    )
    predict_sal.loc[supported] = (
        (salinity_local * support_weight).sum(axis=1).loc[supported] / weight_sum.loc[supported]
    )

    predict_spd = pd.Series(
        sw.svel(predict_sal.values, predict_temp.values, target_pressure.values),
        index=temperature_local.index,
        name="sound_speed",
    )

    predicts = pd.concat([predict_temp, predict_sal, predict_spd], axis=1)
    diagnostics = {
        "scored_depth_count": int((supported).sum()),
        "dropped_depth_count": int((~supported).sum()),
    }

    if diagnostics["scored_depth_count"] == 0:
        return None, diagnostics

    return predicts, diagnostics


def predict_cycle_relaxed_archive(
    cycle_id: str,
    cycle_metadata: pd.DataFrame,
    temp_grid: pd.DataFrame,
    sal_grid: pd.DataFrame,
    pressure_grid: pd.DataFrame,
    sound_speed_grid: pd.DataFrame,
    cfg: HoldoutConfig,
) -> tuple[pd.DataFrame | None, dict, dict | None]:
    context, diagnostics = build_cycle_context(
        cycle_id=cycle_id,
        cycle_metadata=cycle_metadata,
        temp_grid=temp_grid,
        sal_grid=sal_grid,
        pressure_grid=pressure_grid,
        sound_speed_grid=sound_speed_grid,
        cfg=cfg,
    )

    if context is None:
        return None, diagnostics, None

    predicts, predict_diag = predict_cycle_from_context(context)
    target_supported = temp_grid[cycle_id].notna() & sal_grid[cycle_id].notna()
    predicted_supported = predicts["temperature"].notna() & predicts["salinity"].notna() if predicts is not None else False
    diagnostics["scored_depth_count"] = int((target_supported & predicted_supported).sum())
    diagnostics["dropped_depth_count"] = int((target_supported & ~predicted_supported).sum())

    if predicts is None or diagnostics["scored_depth_count"] == 0:
        diagnostics["status"] = "unsupported_depths"
        return None, diagnostics, context

    return predicts, diagnostics, context

# %% [markdown]
# ## 4. Reuse the hold-one-float-out validation frame
#
# Notebook `5` does not introduce a new validation task. Instead, it keeps the same
# hold-one-float-out logic from notebook `4`, because that is still the correct test
# of whether this deterministic backbone is worth carrying into later uncertainty
# work.

# %%
rng = np.random.default_rng(config.random_seed)
platform_numbers = np.sort(active_cycles_metadata["platform_number"].unique())

if config.max_platforms is not None and config.max_platforms < len(platform_numbers):
    platform_numbers = np.sort(rng.choice(platform_numbers, size=config.max_platforms, replace=False))

print(f"Platforms scheduled for evaluation: {len(platform_numbers):,}")

# %%
if cached_model_build_artifact is None:
    cycle_metrics_records = []
    residuals_long_records = []
    diagnostics_records = []
    sample_profiles = {}

    evaluated_cycles = active_cycles_metadata[active_cycles_metadata["platform_number"].isin(platform_numbers)].index
    t = tqdm(evaluated_cycles, total=len(evaluated_cycles))
    for cycle_id in t:
        predicts, diag, context = predict_cycle_relaxed_archive(
            cycle_id=cycle_id,
            cycle_metadata=active_cycles_metadata,
            temp_grid=temp_active_profiles,
            sal_grid=sal_active_profiles,
            pressure_grid=pres_active_profiles,
            sound_speed_grid=sound_speed_profiles,
            cfg=config,
        )
        diagnostics_records.append(diag)

        if predicts is None or context is None:
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
                "weights": context["weights"],
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

# %%
status_counts = diagnostics["status"].value_counts().rename_axis("status").to_frame("n_cycles")
status_counts["share"] = status_counts["n_cycles"] / status_counts["n_cycles"].sum()
status_counts

# %%
cycle_metrics[[
    "temperature_rmse", "salinity_rmse", "sound_speed_rmse",
    "temperature_mae", "salinity_mae", "sound_speed_mae",
]].describe().T

# %% [markdown]
# ## 5. Current model validation summary
#
# Whether notebook `5` rebuilt the model from raw inputs or loaded it from the
# local cache, this section summarizes the deterministic model state now in memory.

# %%
if cached_model_build_artifact is None:
    validation_summary = pd.DataFrame.from_records([{
        "model": "relaxed_weighted_local_window",
        "evaluated_cycles": int(len(cycle_metrics)),
        "skipped_cycles": int((diagnostics["status"] != "ok").sum()),
        "ok_share": float((diagnostics["status"] == "ok").mean()),
        "median_sound_speed_rmse": float(cycle_metrics["sound_speed_rmse"].median()),
        "median_sound_speed_mae": float(cycle_metrics["sound_speed_mae"].median()),
        "median_retained_cycle_count": float(cycle_metrics["retained_cycle_count"].median()),
        "median_effective_cycle_count": float(cycle_metrics["effective_cycle_count"].median()),
        "median_dropped_depth_count": float(cycle_metrics["dropped_depth_count"].median()),
    }]).set_index("model")
validation_summary

# %% [markdown]
# ## 6. Model-integrity checks
#
# The point here is not to reprove the notebook `4` metrics from scratch. It is to
# verify that the saved deterministic ingredients are coherent enough to serve as a
# stable handoff point for later uncertainty mechanics.

# %%
shared_columns_ok = (
    temp_active_profiles.columns.equals(sal_active_profiles.columns)
    and temp_active_profiles.columns.equals(pres_active_profiles.columns)
    and temp_active_profiles.columns.equals(sound_speed_profiles.columns)
)
shared_index_ok = (
    temp_active_profiles.index.equals(sal_active_profiles.index)
    and temp_active_profiles.index.equals(pres_active_profiles.index)
    and temp_active_profiles.index.equals(sound_speed_profiles.index)
)

print(f"Shared cycle order across model tables: {shared_columns_ok}")
print(f"Shared depth index across model tables: {shared_index_ok}")

# %%
sample_cycle_ids = list(cycle_metrics.index[: min(5, len(cycle_metrics))])
integrity_records = []
sample_contexts = {}

for cycle_id in sample_cycle_ids:
    predicts, diag, context = predict_cycle_relaxed_archive(
        cycle_id=cycle_id,
        cycle_metadata=active_cycles_metadata,
        temp_grid=temp_active_profiles,
        sal_grid=sal_active_profiles,
        pressure_grid=pres_active_profiles,
        sound_speed_grid=sound_speed_profiles,
        cfg=config,
    )

    actuals = pd.concat([
        temp_active_profiles[cycle_id].rename("temperature"),
        sal_active_profiles[cycle_id].rename("salinity"),
        sound_speed_profiles[cycle_id].rename("sound_speed"),
    ], axis=1)
    residuals = predicts - actuals

    sample_contexts[cycle_id] = {
        "target_meta": context["target_meta"],
        "local_metadata": context["local_metadata"],
        "weights": context["weights"],
        "weight_sum": context["weight_sum"],
        "depthwise_effective_cycle_count": context["depthwise_effective_cycle_count"],
        "temperature_local": context["temperature_local"],
        "salinity_local": context["salinity_local"],
        "pressure_local": context["pressure_local"],
        "sound_speed_local": context["sound_speed_local"],
    }

    integrity_records.append({
        "cycle_id": cycle_id,
        "same_platform_leak": bool(
            (context["local_metadata"]["platform_number"] == context["target_meta"]["platform_number"]).any()
        ),
        "cached_scored_depth_count": int(cycle_metrics.loc[cycle_id, "scored_depth_count"]),
        "recomputed_scored_depth_count": int(diag["scored_depth_count"]),
        "cached_sound_speed_rmse": float(cycle_metrics.loc[cycle_id, "sound_speed_rmse"]),
        "recomputed_sound_speed_rmse": float(np.sqrt(np.nanmean(residuals["sound_speed"] ** 2))),
    })

integrity_checks = pd.DataFrame.from_records(integrity_records)
if not integrity_checks.empty:
    integrity_checks = integrity_checks.set_index("cycle_id")
    integrity_checks["rmse_abs_diff"] = (
        integrity_checks["cached_sound_speed_rmse"] - integrity_checks["recomputed_sound_speed_rmse"]
    ).abs()
integrity_checks

# %%
fig, ax = plt.subplots(figsize=(8, 4))
cycle_metrics["sound_speed_rmse"].hist(ax=ax, bins=30, color="#4c78a8", alpha=0.85)
ax.axvline(cycle_metrics["sound_speed_rmse"].median(), color="crimson", linestyle="--", linewidth=1.2)
ax.set_title("Notebook 5 model-build holdout summary")
ax.set_xlabel("Cycle sound-speed RMSE (m/s)")
ax.set_ylabel("Held-out cycles")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 7. Save or reuse the deterministic model-build cache
#
# The saved artifact deliberately contains tables and diagnostics, not executable
# functions. The later uncertainty notebook can reload this pickle and then reuse
# the helper cells in this notebook to build whatever passthrough representation is
# actually desired.

# %%
model_build_artifact = {
    "config": asdict(config),
    "depth_grid": depth_grid.to_numpy(),
    "cycle_metadata": active_cycles_metadata,
    "temperature_profiles": temp_active_profiles,
    "salinity_profiles": sal_active_profiles,
    "pressure_profiles": pres_active_profiles,
    "sound_speed_profiles": sound_speed_profiles,
    "validation_cycle_metrics": cycle_metrics,
    "validation_depth_metrics": depth_metrics,
    "validation_diagnostics": diagnostics,
    "validation_summary": validation_summary,
    "integrity_checks": integrity_checks,
    "sample_contexts": sample_contexts,
}

if cached_model_build_artifact is None:
    with model_cache_file.open("bw") as f:
        pickle.dump(model_build_artifact, f)
    print(f"Saved deterministic model-build cache to: {model_cache_file}")
else:
    print(f"Reused deterministic model-build cache at: {model_cache_file}")

# %% [markdown]
# ## 8. Handoff boundary
#
# At this point the deterministic local-window model is built, validated in the
# same holdout frame used by notebook `4`, and exported as a stable input package.
#
# The next notebook can now focus narrowly on the uncertainty passthrough mechanics:
# - which upstream uncertainty terms to admit
# - how to carry them through the local weighted prediction step
# - whether the resulting spread is better represented as per-depth standard
#   deviations, intervals, covariance, or ensembles
#
# That later notebook should not need to revisit the deterministic archive build
# unless the local model choice itself changes.
