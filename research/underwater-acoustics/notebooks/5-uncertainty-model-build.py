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
# # Deterministic weighted local-window model build
#
# This notebook is the fifth step in the current `underwater-acoustics` sequence. Its role is narrower than the replication and holdout notebooks that come before it: it rebuilds the relaxed weighted local-window predictor as a reusable deterministic backbone for later downstream use, rather than as a standalone acoustics result. That sequence placement follows the topic notebook index in [README.md](README.md).
#
# The notebook should therefore be read as a model-build handoff artifact, not as the canonical summary of the acoustics topic. Source-backed synthesis still lives in [../literature-review.md](../literature-review.md), while the surrounding implementation rationale lives in [../notes/jana-replication-notes.md](../notes/jana-replication-notes.md) and [../notes/literature-review-project-framing-notes.md](../notes/literature-review-project-framing-notes.md).
#
# %% [markdown]
# ## Why this notebook exists
#
# The canonical literature review argues that the profile-level interpolation step in Argo-to-sound-speed workflows is often under-reported even though adjacent literature shows that interpolation choice can materially affect derived ocean-state quantities and downstream diagnostics. See [Vertical Interpolation Methods Remain Under-Reported](../literature-review.md#vertical-interpolation-methods-remain-under-reported) and the review conclusion in [literature-review.md](../literature-review.md#conclusion).
#
# The project-facing implication extracted in [literature-review-project-framing-notes.md](../notes/literature-review-project-framing-notes.md) is that the useful contribution here is not to restate that sound speed matters, but to make one explicit processing path inspectable, reproducible, and eventually uncertainty-aware. That framing is also consistent with [Uncertainty Quantification: Sensor Precision Versus Mapping Error](../literature-review.md#uncertainty-quantification-sensor-precision-versus-mapping-error), [Acoustic Applications Increasingly Depend on Argo](../literature-review.md#acoustic-applications-increasingly-depend-on-argo), and the `argopy` tooling discussion in the same review.
#
# %% [markdown]
# ## Method boundary
#
# Notebook `1` established the calibrated Jana et al. (2022) replication baseline, notebooks `2` through `4` converted that baseline into held-out local prediction experiments, and this notebook repackages the currently preferred relaxed weighted-local-window path as a deterministic model surface. That handoff matches the extension path described in [jana-replication-notes.md](../notes/jana-replication-notes.md).
#
# Two boundaries matter here:
# - This notebook is not a new literature-review artifact; source-backed claims should still trace through [../literature-review.md](../literature-review.md).
# - This notebook is not yet the full uncertainty-propagation endpoint promised by the broader acoustics framing; it is the deterministic backbone that later uncertainty work can attach to.
#
# The equation comparison is intentionally kept visible. The Jana-facing baseline remains tied to the legacy EOS-80 / UNESCO sound-speed path, while TEOS-10 / GSW is kept alongside it as an upgrade path so equation-choice effects are not silently conflated with interpolation and weighting effects. See [Sound Speed Equations: From UNESCO to TEOS-10](../literature-review.md#sound-speed-equations-from-unesco-to-teos-10) and the recommendation section in [jana-replication-notes.md](../notes/jana-replication-notes.md).
#
# %% [markdown]
# ## Current uncertainty scope
#
# The current error-architecture note distinguishes three main uncertainty terms for the broader package path: spatiotemporal interpolation error, observation error propagated through kernel weights, and kernel-parameter uncertainty. See [error-propagation-architecture-notes.md](../notes/error-propagation-architecture-notes.md).
#
# This notebook only covers part of that picture. In its current form it:
# - estimates held-out structural interpolation residuals for temperature and salinity
# - propagates upstream profile-level uncertainty through the linear weighted average using squared weights
# - compares deterministic EOS-80 and TEOS-10 sound-speed outputs on the resulting weighted profiles
#
# It does **not** yet present the full package uncertainty architecture as a completed notebook result, and it does not yet publish a final sound-speed uncertainty field. Those broader claims should remain in note or package-architecture status until they are implemented and validated explicitly.
#
# %%
import pickle
from dataclasses import asdict
from pathlib import Path
import gsw
import seawater as sw
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm.auto import tqdm
import scipy.stats as stats
from itertools import product
from datetime import datetime as dt

# %%
from argo_interp.data import data_filter, get_data
from argo_interp.cycle.adapter import PchipAdapter
from argo_interp.cycle.config import ModelKwargs, ModelSettings
from argo_interp.cycle.domain import ModelData, ModelMeta
from argo_interp.cycle.model import Model
from argo_interp.model import CycleModels, CycleData
from lib import (
    GaussianScale,
    WeightConfig,
    build_candidate_query,
    compute_weight_deltas,
    weighted_cycle_prediction,
    plot_desaturated_heatmap,
)

# %% [markdown]
# ## 1. Load the Bay of Bengal archive and apply the settled QC gate
#
# The first stage keeps the same regional box used throughout the Jana replication sequence. The goal here is not to introduce a new archive definition, but to rebuild the deterministic predictor from the same Bay of Bengal source region that made the earlier notebooks acoustically legible. That continuity matters because the broader Jana-facing rationale is still the main empirical anchor for this topic; see [jana-replication-notes.md](../notes/jana-replication-notes.md).
#
# The fetch path remains intentionally close to the practical `argopy` workflow discussed in the literature review. As summarized in [Vertical Interpolation Methods Remain Under-Reported](../literature-review.md#vertical-interpolation-methods-remain-under-reported), `argopy` is useful enabling infrastructure for Argo data access and reshaping, but it does not itself solve the uncertainty-propagation problem this project is trying to expose.
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

argo_data_path = data_path / "argo_data.pkl"

if argo_data_path.exists():
    # Reuse the cached regional pull when it exists so the notebook can focus on model build rather than redownloading.
    ds = pickle.load(open(argo_data_path, "rb"))
else:
    ds = get_data(box, progress=True)
    with argo_data_path.open("wb") as f:
        pickle.dump(ds, f)

# %%
ds_filters = [
    ds["PRES_QC"].isin([1, 2]),
    ds["TEMP_QC"].isin([1, 2]),
    ds["PSAL_QC"].isin([1, 2]),
]
ds = data_filter(ds, ds_filters)

# %% [markdown]
# ## 2. Fit one profile model per retained cycle
#
# This stage converts the screened archive into a bank of per-cycle interpolation models. The notebook is still operating in the same conceptual space highlighted in [Vertical Interpolation Methods Remain Under-Reported](../literature-review.md#vertical-interpolation-methods-remain-under-reported): the project contribution lives at the profile-processing layer between native Argo observations and derived sound-speed structure.
#
# For notebook `5`, the goal is not to compare multiple interpolation families again. Instead, it picks one deterministic path and turns it into a reusable cycle collection that downstream local predictions can query repeatedly. That is why the notebook shifts from the descriptive and benchmark role of notebooks `1-4` into a model-build role.
#
# %%
settings = ModelSettings(n_folds=5)

# %%
models = {}
models_data = {}

cycles = len(ds[["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"]].to_dataframe().drop_duplicates())
t = tqdm(ds.groupby(["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"]), total=cycles)
for (platform_number, cycle_number, direction), cycle_ds in t:
    pressure = cycle_ds["PRES"].values
    temperature = cycle_ds["TEMP"].values
    salinity = cycle_ds["PSAL"].values

    latitude = cycle_ds["LATITUDE"].values[0]
    longitude = cycle_ds["LONGITUDE"].values[0]
    timestamp = cycle_ds["TIME"].values[0]

    if cycle_ds.sizes['N_POINTS'] < 3:
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

    linear_model = Model.build(model_meta, model_data, PchipAdapter, settings)
    models[cycle_id] = linear_model
    models_data[cycle_id] = model_data
    t.set_postfix(model_count=len(models))
cycle_models = CycleModels(models)
all_metadata = cycle_models.metadata()

# %% [markdown]
# ## 3. Recreate the held-out local-prediction frame
#
# Before exporting a deterministic model surface, the notebook first reuses the local-window logic from the earlier holdout notebooks to estimate how much structural interpolation error remains when one cycle is predicted from nearby cycles. This is the first of the uncertainty terms described in [error-propagation-architecture-notes.md](../notes/error-propagation-architecture-notes.md): spatiotemporal interpolation error estimated from held-out residuals rather than from upstream sensor uncertainty.
#
# The weighting configuration is carried over as a practical working choice, not as a newly justified set of source-backed constants. That matches the project-note boundary already stated around the weighted extensions in the earlier acoustics notebooks.
#
# %%
SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60
SECONDS_PER_WEEK = 7 * 24 * 60 * 60

dist_rad = 1
dist_border_stdev = 3

year_stdev = 3

season_weeks = 8
season_week_stdev = 3

use_distance_weight = True
use_time_weight = False
use_season_weight = False

weight_config = WeightConfig(
    distance=GaussianScale.from_border(dist_rad, dist_border_stdev),
    time=GaussianScale(year_stdev * SECONDS_PER_YEAR),
    season=GaussianScale.from_border(season_weeks * SECONDS_PER_WEEK, season_week_stdev),
    use_distance=use_distance_weight,
    use_time=use_time_weight,
    use_season=use_season_weight,
)


# %%
temp_errors = {}
temp_rmse_vals = {}
sal_errors = {}
sal_rmse_vals = {}
for cycle_position, cycle_id in enumerate(tqdm(all_metadata.cycle_id)):
    model_data = models_data[cycle_id]
    target_timestamp = pd.Timestamp(all_metadata.timestamp[cycle_position])
    candidate_query = build_candidate_query(
        target_latitude=all_metadata.latitude[cycle_position],
        target_longitude=all_metadata.longitude[cycle_position],
        # target_timestamp=target_timestamp,
        dist_rad=dist_rad,
        # season_weeks=season_weeks,
        exclude_platform_number=all_metadata.platform_number[cycle_position],
    )
    candidate_mask = cycle_models.mask(**candidate_query.to_mask_kwargs())
    candidate_metadata = cycle_models.metadata(candidate_mask)

    if len(candidate_metadata) == 0:
        continue

    weight_deltas = compute_weight_deltas(
        target_latitude=all_metadata.latitude[cycle_position],
        target_longitude=all_metadata.longitude[cycle_position],
        target_timestamp=all_metadata.timestamp[cycle_position],
        candidate_metadata=candidate_metadata,
    )
    total_weight = weight_config.joint_weight(weight_deltas)

    # Only score depths that are supported by at least one neighboring profile in the retained local set.
    support_mask = (
        (model_data.pressure[:, None] >= candidate_metadata.pressure_min[None, :]) &
        (model_data.pressure[:, None] <= candidate_metadata.pressure_max[None, :])
    ).any(axis=1)

    if not np.any(support_mask):
        continue

    active_pressure = model_data.pressure[support_mask]
    active_temperature = model_data.temperature[support_mask]
    active_salinity = model_data.salinity[support_mask]

    interpolates = cycle_models.interpolate(active_pressure, mask=candidate_mask)
    predict_temperature, predict_salinity = weighted_cycle_prediction(interpolates, total_weight)

    predict_temp = pd.Series(
        predict_temperature,
        index=active_pressure,
        name="temperature",
    )
    predict_sal = pd.Series(
        predict_salinity,
        index=active_pressure,
        name="salinity",
    )

    temp_error = active_temperature - predict_temp
    sal_error = active_salinity - predict_sal

    temp_errors[cycle_id] = temp_error
    sal_errors[cycle_id] = sal_error

    temp_rmse = np.sqrt((temp_error ** 2).mean())
    sal_rmse = np.sqrt((sal_error ** 2).mean())

    temp_rmse_vals[cycle_id] = temp_rmse
    sal_rmse_vals[cycle_id] = sal_rmse

temp_errors_straight = pd.concat(temp_errors.values(), axis=0)
sal_errors_straight = pd.concat(sal_errors.values(), axis=0)
temp_rmse_vals = pd.Series(temp_rmse_vals)
sal_rmse_vals = pd.Series(sal_rmse_vals)

# %%
fig, ax = plt.subplots(ncols=2, figsize=(12, 5))

sns.scatterplot(x=temp_errors_straight.values, y=temp_errors_straight.index.values, ax=ax[0], alpha=0.25)
ax[0].invert_yaxis()

sns.scatterplot(x=sal_errors_straight.values, y=sal_errors_straight.index.values, ax=ax[1], alpha=0.25)
ax[1].invert_yaxis()

fig.tight_layout()

# %%
temp_rmse_vals.mean(), sal_rmse_vals.mean()

# %% [markdown]
# ## 4. Build the deterministic local model on a regular latitude-longitude grid
#
# Once the notebook has a retained cycle bank and a holdout-style local prediction rule, it evaluates that rule on a regular grid across the Bay of Bengal. The purpose here is operational rather than inferential: produce a deterministic surface that later workflows can query without rerunning the full notebook chain each time.
#
# This is the point where the notebook starts to resemble a lightweight regional model-build artifact rather than a replication notebook. That transition is consistent with the topic README, which already treats notebook `5` as a handoff into broader model-building work rather than as the canonical acoustics case study.
#
# %%
lat_resolution = 1e-1
lon_resolution = 1e-1

lat_array = np.arange(box[2], box[3] + lat_resolution, lat_resolution)
lon_array = np.arange(box[0], box[1] + lon_resolution, lon_resolution)

depth_array = np.array([5, 35, 110, 500])

# %%
lat_lon_product = list(product(lat_array, lon_array))

# %%
anchor_date = dt.now()
results = []
for lat, lon in tqdm(lat_lon_product):
    candidate_query = build_candidate_query(
        target_latitude=lat,
        target_longitude=lon,
        dist_rad=dist_rad,
    )
    candidate_mask = cycle_models.mask(**candidate_query.to_mask_kwargs())

    if candidate_mask.sum() == 0:
        continue

    candidate_metadata = cycle_models.metadata(candidate_mask)

    weight_deltas = compute_weight_deltas(
        target_latitude=lat,
        target_longitude=lon,
        target_timestamp=np.datetime64(anchor_date),
        candidate_metadata=candidate_metadata,
    )
    total_weight = weight_config.joint_weight(weight_deltas)
    scaled_weight = total_weight / total_weight.sum()

    interpolates = cycle_models.interpolate(depth_array, mask=candidate_mask)
    predict_temperature, predict_salinity = weighted_cycle_prediction(interpolates, total_weight)

    interp_errors = cycle_models.interp_error(depth_array, mask=candidate_mask)
    # For a linear weighted average, independent upstream variances propagate through squared weights.
    interp_var = CycleData(
        temperature=interp_errors.temperature**2,
        salinity=interp_errors.salinity**2,
    )
    var_temperature, var_salinity = weighted_cycle_prediction(interp_var, total_weight**2)

    c1 = sw.svel(predict_salinity, predict_temperature, depth_array)

    SA = gsw.SA_from_SP(predict_salinity, depth_array, lon, lat)
    CT = gsw.CT_from_t(SA, predict_temperature, depth_array)
    c2 = gsw.sound_speed(SA, CT, depth_array)

    results.append({'latitude': lat, 'longitude': lon,
                    'temp_val': predict_temperature,
                    'temp_var': var_temperature,
                    'sal_val': predict_salinity,
                    'sal_var': var_salinity,
                    'sound_speed_eos80': c1,
                    'sound_speed_teos10': c2,
                    'support': total_weight.sum()})

# %% [markdown]
# ## 5. Compare deterministic equation paths and visualize support
#
# The last stage reshapes the gridded results for plotting. The side-by-side EOS-80 and TEOS-10 sound-speed outputs are here to preserve the baseline-versus-upgrade framing described in [Sound Speed Equations: From UNESCO to TEOS-10](../literature-review.md#sound-speed-equations-from-unesco-to-teos-10) and in [jana-replication-notes.md](../notes/jana-replication-notes.md). The notebook is not trying to settle that equation comparison here; it is keeping the distinction visible so interpolation and weighting choices are not silently mixed with equation-of-state choices.
#
# The support field is also plotted explicitly because this notebook is still closer to transparent model construction than to a finished mapped product. The reader should be able to see not only the predicted sound-speed field, but also where that field is backed by stronger or weaker local retained support.
#
# The project's methodological default remains pressure-space interpolation and prediction, consistent with the Argo-native vertical coordinate discussed in the literature review. In this notebook, labels such as `~110 m` should therefore be read as approximate acoustics-facing depth interpretations used for readability in an exploratory slice visualization, not as exact geometric-depth claims or as a standalone proof that the local model has been fully reformulated onto a strict depth coordinate.
#
# %%
idx = 2
chart_data = pd.DataFrame([{
    'latitude': result['latitude'],
    'longitude': result['longitude'],
    'temperature': result['temp_val'][idx],
    'temp_var': result['temp_var'][idx],
    'salinity': result['sal_val'][idx],
    'sal_var': result['sal_var'][idx],
    'sound_speed_eos80': result['sound_speed_eos80'][idx],
    'sound_speed_teos10': result['sound_speed_teos10'][idx],
    'support': result['support'],
} for result in results])

# %%
chart_data.pivot(index='latitude', columns='longitude', values='temp_var').mean().mean()

# %%
temp_matrix = chart_data.pivot(index='latitude', columns='longitude', values='temperature')
sal_matrix = chart_data.pivot(index='latitude', columns='longitude', values='salinity')
sound_eos80 = chart_data.pivot(index='latitude', columns='longitude', values='sound_speed_eos80')
sound_teos10 = chart_data.pivot(index='latitude', columns='longitude', values='sound_speed_teos10')
support_matrix = chart_data.pivot(index='latitude', columns='longitude', values='support')

tau = 40
support_matrix = 1 - np.exp(-support_matrix / tau)

# %%
import cartopy.crs as ccrs

light_mode = True
neutral_color = (0.94, 0.94, 0.94) if light_mode else (0.25, 0.25, 0.25)
land_color = "0.75" if light_mode else "0.85"
val_min_max = (1522.0, 1530.0)

fig, ax = plt.subplots(
    figsize=(10, 7.5),
    subplot_kw={"projection": ccrs.PlateCarree()},
)
fig.patch.set_facecolor("white" if light_mode else (0.1, 0.1, 0.1))

_ = plot_desaturated_heatmap(
    values=sound_eos80,
    value_vmin=val_min_max[0], value_vmax=val_min_max[1],
    standard_error=support_matrix,
    title="Bay of Bengal"
          "\nSound Speed (m/s) at ~110m"
          "\nAveraged across 2011 - 2020",
    cbar_label="Sound Speed (m/s)",
    cmap='jet',
    add_colorbar=True,
    ax=ax,
    neutral_color=neutral_color,
    light_mode=light_mode,
    add_gridlines=True,
    gridline_labels=True,
    add_land=True,
    land_color=land_color,
    add_coastline=True,
    extent=(80, 99, 6, 23),
    font_scale=1.3,
)

fig.tight_layout()

fig.savefig(chart_path / 'jana_remake_image.jpg', facecolor=fig.get_facecolor(),
            dpi=300)

# %% [markdown]
# ## 6. Sequence handoff
#
# Read as a full chain, the five notebooks now divide the acoustics work into distinct slices:
# - notebook `1`: establish the calibrated Jana replication baseline
# - notebook `2`: measure how far the flat Jana-style kernel can go as a held-out predictor
# - notebook `3`: test whether weighting improves that benchmark under the same strict archive
# - notebook `4`: test whether the weighted predictor improves further when partial local support is retained
# - notebook `5`: take the current preferred deterministic path and turn it into a reusable model-build artifact
#
# That means this notebook is the end of the current sequence, but not the end of the broader work. Its handoff is into the next stage of the project:
# - attach the fuller uncertainty architecture described in [../notes/error-propagation-architecture-notes.md](../notes/error-propagation-architecture-notes.md)
# - decide which outputs should stay as acoustics-facing notebook artifacts and which should migrate into a broader spatiotemporal model-build topic
# - keep equation choice, interpolation choice, and uncertainty propagation separated clearly enough that later notebooks or package outputs can compare them explicitly rather than absorbing them into one opaque workflow
# - treat the current plotted `~depth` slices as exploratory presentation outputs until the coordinate treatment is tightened further
#
# %%
