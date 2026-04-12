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
#     version: 3.11.13
# ---

# %% [markdown]
# # 01. Argo Cycle Representation Baseline
#
# This notebook establishes the baseline case for a custom curvature-adaptive least-squares spline representation of individual Argo profiles.
#
# **Core question**: can a per-cycle spline artifact be made compact, queryable, and uncertainty-aware while still reproducing the large-scale vertical structure of observed profiles well enough to be useful?
#
# **Approach**: adaptive B-spline fitting with curvature-guided knot placement informed by Li et al. (2005), least-squares fitting rather than exact interpolation, and a local uncertainty construction based on model residuals plus Argo delayed-mode sensor conventions (Wong et al., 2025, pp. 43, 47, 50, 55-56, 84).
#
# **Context**: this sits closer to Yarger et al. (2022, pp. 11-12, 216-218) than to exact interpolants such as MRST-PCHIP, because the design target is a stored functional representation of a profile rather than exact reproduction of every retained observation.
#
# **Scope**: this notebook is intentionally method-internal. Its job is to show that the custom spline idea can be fit, queried, and inspected coherently on a real Argo sample before asking how it compares to other approaches. Direct benchmarking against Akima and PCHIP is deferred to notebook 02.
#
#

# %% [markdown]
# ## 1. Dependencies
#
#

# %%
import numpy as np
from argopy import DataFetcher as ArgoDataFetcher
import pandas as pd
from tqdm.auto import tqdm
from matplotlib import pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle

# %%
from lib import ModelError, SensorError, CycleError, CycleModel, CycleSettings
from lib import build_model, calc_fold_error

from argo_interp.data import get_data

# %% [markdown]
# ## 2. Data Acquisition
#
# Request Argo profiles from a bounded region and time window. This slice provides a reproducible working dataset for method development and internal validation.
#
# **Regional context**: this subtropical box (20-30°N, 75-45°W) is used here as a practical starting point for local method development rather than as a literature-backed claim about the easiest or most representative Argo regime. Performance in more difficult settings such as deep winter mixed layers, equatorial inversions, and polar haloclines remains future validation work.
#
#

# %%
data_path = Path('./data')
data_path.mkdir(exist_ok=True)

data_file = data_path / 'argo_data.pkl'

# %%
override = False

if data_file.exists() and not override:
    with data_file.open('br') as f:
        ds = pickle.load(f)
else:
    box = [
        -75, -45, ## Longitude min/max
        20, 30, ## Latitude min/max
        0, 3000, ## Pressure/depth min/max
        '2011-01', '2011-06', ## Datetime min/max
    ]
    ds = get_data(box, progress=True)

    with data_file.open('bw') as f:
        pickle.dump(ds, f)

# %%
data = ds.to_dataframe()

# %% [markdown]
# ## 3. Profile Structure
#
# Transform flat observation rows into cycle-indexed profiles:
# - unique cycle identifier (`PLATFORM_CYCLE`)
# - cycle metadata (position, time)
# - pressure-sorted readings for model fitting
#
#

# %%
group_col = 'PLATFORM_CYCLE'
group_fields = ['PLATFORM_NUMBER', 'CYCLE_NUMBER']
cycle_fields = ['LATITUDE', 'LONGITUDE', 'TIME']
reading_fields = ['PRES', 'PRES_ERROR', 'PSAL', 'PSAL_ERROR', 'TEMP', 'TEMP_ERROR']

# %%
cycles = data[group_fields + cycle_fields].drop_duplicates().sort_values(group_fields)
cycles.index = (cycles[group_fields[0]].astype(str) + '-' + cycles[group_fields[1]].astype(str)).rename('PLATFORM_CYCLE')

# %%
readings = data[group_fields + reading_fields].drop_duplicates().sort_values([*group_fields, 'PRES']).reset_index(drop=True)
readings.insert(0, group_col, readings[group_fields[0]].astype(str) + '-' + readings[group_fields[1]].astype(str))
readings = readings.drop(columns=group_fields)

# %% [markdown]
# ## 4. Cycle-Level Model Fitting
#
# For each profile:
# 1. estimate validation error via 5-fold cross-validation
# 2. fit temperature and salinity spline models
# 3. package the resulting models with uncertainty metadata in `CycleModel` objects
#
# The immediate result is a compact per-cycle artifact that can be queried by pressure rather than a method comparison claim.
#
# ### Method Overview
#
# The working intuition is that Argo profiles have mixed structure: thermoclines bend sharply, while deep layers are often comparatively smooth. Rather than spreading knots uniformly, the custom method places more flexibility where curvature is highest and fewer degrees of freedom in flatter regions. That follows curvature-adaptive spline ideas from Li et al. (2005, pp. 791-794), used here as a cross-domain methodological analogue rather than direct oceanographic prior art.
#
# Least-squares fitting is used rather than exact interpolation. Exact interpolants such as MR-PCHIP and MRST-PCHIP are designed to reconstruct values between retained observations while limiting overshoot and preserving physically realistic structure (Barker & McDougall, 2020, pp. 1-2, 4-7, 14-15). This notebook asks a different question: can a non-exact fit still produce a coherent stored profile representation with sensible uncertainty behavior?
#
# Uncertainty combines model error, an instrument/error term, and pressure-gradient propagation. For temperature, the instrument term is fixed at 0.002°C. For salinity, this notebook does not use a single universal constant because delayed-mode salinity uncertainty is treated as adjustment-dependent with a minimum floor rather than one exact value everywhere (Wong et al., 2025, pp. 50, 55-56, 84; Wong et al., 2023, p. 9). Instead, it uses the 95th percentile of each cycle's `PSAL_ERROR` values. As a result, the local uncertainty construction is largest where vertical gradients are steepest.
#
# In this local sample, the custom method typically uses 9-16 knots per cycle (median about 9), compared with the 200 equispaced knots used in Yarger et al.'s (2022, pp. 11-12) vertical smoother.
#
# ### Parameter Choices
#
# The `CycleSettings` used here (`prominence=0.25`, `window=10`, `spacing=5.0`, `peak_dist=20`, `folds=5`) were selected through informal experimentation on a subset of profiles. These values should be read as working prototype settings rather than as a globally tuned optimum.
#
# That limitation is acceptable for notebook 01 because the goal here is feasibility: fit the method, inspect the resulting artifact, and see whether the internal diagnostics are coherent enough to justify a broader comparison.
#
#

# %%
settings = CycleSettings(
    prominence = 0.25,
    window = 10,
    spacing = 5.0,
    peak_dist = 20,
    folds = 5,
)

cycle_models = {}
for cycle_number, cycle_data in tqdm(readings.groupby('PLATFORM_CYCLE')):
    cycle_data = cycle_data.sort_values('PRES')
    rmse_temp, rmse_sal = calc_fold_error(cycle_data, settings)

    model_temp = build_model(cycle_data['PRES'], cycle_data['TEMP'], settings)
    model_sal = build_model(cycle_data['PRES'], cycle_data['PSAL'], settings)

    sal_95_error = np.nanpercentile(cycle_data['PSAL_ERROR'], 95)

    cycle_error = CycleError(
        model=ModelError(
            temperature=rmse_temp,
            salinity=rmse_sal,
        ),
        sensor=SensorError(
            salinity=sal_95_error,
        ),
    )
    cycle_model = CycleModel(
        temperature=build_model(cycle_data['PRES'], cycle_data['TEMP'], settings),
        salinity=build_model(cycle_data['PRES'], cycle_data['PSAL'], settings),
        error=cycle_error,
        settings=settings,
        pressure_bounds=(cycle_data['PRES'].min(), cycle_data['PRES'].max()),
    )
    cycle_models[cycle_number] = cycle_model

# %% [markdown]
# ## 5a. Single-Cycle Inspection
#
# Select one cycle for detailed examination. Before comparing this method to anything else, the first check is whether the fitted profile and attached uncertainty behave sensibly on an individual example.
#
#

# %%
# cycle_number = np.random.choice(list(cycle_models.keys()))
cycle_number = '6900551-71'
print(f"Cycle #: {cycle_number}")
cycle_data = readings.loc[readings['PLATFORM_CYCLE'] == cycle_number]
cycle_model = cycle_models[cycle_number]

# %%
cycle_interp = cycle_model.interpolate(cycle_data['PRES'])

# %% [markdown]
# ## 5b. Uncertainty Envelope Construction
#
# Construct plotting bands from per-point error terms. Use 2σ as a readable approximation of a likely range around each estimate, not as a formal calibrated confidence interval.
#
# **Depth-varying uncertainty**: the envelope widens in the thermocline where `|dT/dP|` is large, reflecting the fact that a fixed pressure uncertainty of 2.4 dbar contributes more to temperature uncertainty where gradients are steep. In the flat deep ocean where `dT/dP -> 0`, the pressure-propagated term vanishes and only the fixed instrument/error term plus model residuals remain. The pressure and temperature source terms used here come from the delayed-mode Argo QC conventions summarized in Wong et al. (2025, pp. 43, 47, 50, 84).
#
# The three error terms are combined as root-sum-square (RSS) for each query. That independence assumption is a simplification, but it is enough for this notebook's goal of testing whether the method yields uncertainty fields that are at least qualitatively interpretable.
#
#

# %%
sd_offset = 2

cycle_interp['temp_low'] = (cycle_interp['temperature'] - (sd_offset * cycle_interp['temp_error']))
cycle_interp['temp_high'] = (cycle_interp['temperature'] + (sd_offset * cycle_interp['temp_error']))
cycle_interp['sal_low'] = (cycle_interp['salinity'] - (sd_offset * cycle_interp['sal_error']))
cycle_interp['sal_high'] = (cycle_interp['salinity'] + (sd_offset * cycle_interp['sal_error']))

# %% [markdown]
# ## 5c. Visual Diagnostic
#
# Plot the interpolated curves with 2σ envelopes. Pressure increases downward. Where the bands widen, the method is signaling greater local uncertainty rather than hiding structurally difficult regions behind a single global RMSE number.
#
#

# %%
fig, ax = plt.subplots(ncols=2, figsize=(12, 6))

cycle_interp.reset_index().plot(x='temperature', y='pressure', color='#1f78b4', ax=ax[0])
ax[0].fill_betweenx(y=cycle_interp.index, x1=cycle_interp['temp_low'], x2=cycle_interp['temp_high'], color='#a6cee3', alpha=0.5)
cycle_data.plot(x='TEMP', y='PRES', color='#fb9a99', alpha=0.75, ax=ax[0])
ax[0].set(
    title=f"Temperature by Depth, actual vs interpolated."
          f"\nCycle # {cycle_number}",
    xlabel=f"Temperature (c)",
    ylabel=f"Pressure (dbar)",
)
ax[0].invert_yaxis()
ax[0].legend(["Interpolated", "St Error", "Actual"])

cycle_interp.reset_index().plot(x='salinity', y='pressure', color='#1f78b4', ax=ax[1])
ax[1].fill_betweenx(y=cycle_interp.index, x1=cycle_interp['sal_low'], x2=cycle_interp['sal_high'], color='#a6cee3', alpha=0.5)
cycle_data.plot(x='PSAL', y='PRES', color='#fb9a99', alpha=0.75, ax=ax[1])
ax[1].set(
    title=f"Salinity by Depth, actual vs interpolated."
          f"\nCycle # {cycle_number}",
    xlabel=f"Salinity (PSU)",
    ylabel=f"Pressure (dbar)",
)
ax[1].invert_yaxis()
ax[1].legend(["Interpolated", "St Error", "Actual"])

fig.tight_layout()

# %% [markdown]
# ### Interpretation
#
# On this example, the fitted curve follows the observed profile closely across depth, and the uncertainty band widens in the same regions where the profile is structurally more complex. That is the baseline result notebook 01 needs: the custom method appears internally coherent on a single-cycle inspection rather than obviously pathological.
#
#

# %% [markdown]
# ## 6a. Cross-Cycle Validation: RMSE Distributions
#
# Single-profile inspection is necessary but not sufficient. The next question is whether the method behaves consistently across the sampled cycles or only looks reasonable on a hand-picked example.
#
# **Note**: these values quantify within-profile reconstruction error from 5-fold cross-validation, not spatiotemporal prediction error. At this stage they are being used as internal method diagnostics, not as a claim of superiority over other interpolants.
#
#

# %%
model_error = pd.DataFrame([model.error.model for model in cycle_models.values()])

# %%
pd.concat([
    model_error.mean().rename('mean'),
    model_error.median().rename('median'),
    model_error.std().rename('stdev'),
], axis=1)

# %%
fig, ax = plt.subplots(ncols=2, figsize=(12, 6))

sns.histplot(model_error['temperature'], stat='density', ax=ax[0])
ax[0].set(
    title=f"Temperature model error distribution",
    xlabel=f"Temperature (c)",
)

sns.histplot(model_error['salinity'], stat='density', ax=ax[1])
ax[1].set(
    title=f"Salinity model error distribution",
    xlabel=f"Salinity (PSU)",
)

fig.tight_layout()

# %% [markdown]
# ### Distribution Interpretation
#
# Both RMSE distributions are strongly right-skewed: most cycles fit reasonably well, with a smaller tail of difficult outliers. For notebook 01, that is enough to support a feasibility claim. The method is not failing everywhere; it is working on many profiles while leaving a visible tail that needs follow-up.
#
# **Open question**: the right tail deserves investigation. Potential causes include profiles with strong subsurface inversions, fine-scale layering, or sparse sampling in structurally difficult regions. Notebook 02 will determine how serious that tail is relative to exact-interpolant baselines.
#
#

# %% [markdown]
# ## 6b. Residual Structure by Depth
#
# Aggregate RMSE says how much error there is on average, but not where it occurs. A more useful internal diagnostic is whether the residuals line up with oceanographic complexity rather than appearing arbitrary.
#
# **Question**: if curvature-adaptive knot placement is doing something meaningful, do the larger residuals appear in structurally difficult regions such as the thermocline and inversion layers, while simpler deep-water regions remain easier to fit?
#
# Note: these are model reconstruction residuals only. The total reported uncertainty used elsewhere in the notebook is larger because it also includes sensor and pressure-propagated terms.
#
#

# %%
error_records = []
for cycle_number, cycle_data in tqdm(readings.groupby('PLATFORM_CYCLE')):
    cycle_model = cycle_models[cycle_number]
    cycle_interp = cycle_model.interpolate(cycle_data['PRES'])
    cycle_values = pd.concat([
        cycle_data.set_index('PRES')['TEMP'].rename('temp_actual'),
        cycle_interp['temperature'].rename('temp_interp'),
        cycle_data.set_index('PRES')['PSAL'].rename('sal_actual'),
        cycle_interp['salinity'].rename('sal_interp'),
    ], axis=1).reset_index().rename(columns={'index': 'pressure'})
    cycle_values['temp_error'] = cycle_values['temp_actual'] - cycle_values['temp_interp']
    cycle_values['sal_error'] = cycle_values['sal_actual'] - cycle_values['sal_interp']
    error_records.append(cycle_values[['pressure', 'temp_error', 'sal_error']])
error_records = pd.concat(error_records, axis=0)

# %%
pd.concat([
    error_records[['temp_error', 'sal_error']].mean().rename('mean'),
    error_records[['temp_error', 'sal_error']].median().rename('median'),
    error_records[['temp_error', 'sal_error']].std().rename('stdev'),
], axis=1)

# %%
fig, ax = plt.subplots(ncols=2, figsize=(12, 6))

ax[0].hexbin(error_records['temp_error'], error_records['pressure'], gridsize=35, mincnt=1, cmap='viridis')
ax[0].invert_yaxis()
ax[0].set(
    title=f"Temperature Interpolation Error by Pressure",
    xlabel=f"Temperature (c)",
    ylabel=f"Pressure (dbar)",
)

ax[1].hexbin(error_records['sal_error'], error_records['pressure'], gridsize=35, mincnt=1, cmap='viridis')
ax[1].invert_yaxis()
ax[1].set(
    title=f"Salinity Interpolation Error by Pressure",
    xlabel=f"Salinity (PSU)",
    ylabel=f"Pressure (dbar)",
)

fig.tight_layout()

# %% [markdown]
# ### Interpretation
#
# The residual plots show depth-structured behavior rather than obvious global bias: aggregate central tendency remains near zero, while the larger spread appears in the same depth ranges where profile structure is more complex. That is the kind of pattern the custom method was meant to produce.
#
# This does not prove that the custom spline is the best available approach. It does show that the method behaves like a plausible profile representation rather than an arbitrary compression scheme, which is the threshold notebook 01 is meant to test.
#
#

# %% [markdown]
# ## 7. Method Scope and Current Limitations
#
# **What this notebook demonstrates**
# - proof of concept for a custom adaptive spline representation of Argo profiles
# - a working per-cycle artifact with queryable uncertainty fields
# - internal cross-validation and residual diagnostics across many cycles
# - enough coherence to justify benchmarking the method against more traditional interpolants
#
# **What this notebook does not establish**
# - whether this method is stronger or weaker than Akima, PCHIP, or other baselines
# - how the high-error tail compares to simpler exact-interpolant methods
# - whether the uncertainty construction is calibrated rather than just interpretable
# - whether the method generalizes beyond this one regional sample
# - whether the curvature-adaptive machinery is worth its complexity
#
# **Intended use**: notebook 01 should be read as a method-confirmation notebook. It shows that the custom spline idea is viable enough to deserve comparison, not that it has already won that comparison.
#
#

# %% [markdown]
# ## References
#
# **Reference status note**: all references listed here were checked against local full-text copies. The Li et al. (2005) comparison remains a cross-domain methodological analogue rather than an oceanographic source claim.
#
# - Barker, P. M., & McDougall, T. J. (2020). *Two interpolation methods using multiply-rotated piecewise cubic Hermite interpolating polynomials.* Journal of Atmospheric and Oceanic Technology, 37(4), 605-619. https://doi.org/10.1175/JTECH-D-19-0211.1
# - Li, W., Xu, S., Zhao, G., & Goh, L. P. (2005). *Adaptive knot placement in B-spline curve approximation.* Computer-Aided Design, 37(8), 791-797. https://doi.org/10.1016/j.cad.2004.09.008
# - Thielmann, A., Kneib, T., & Saefken, B. (2025). *Enhancing adaptive spline regression: An evolutionary approach to optimal knot placement and smoothing parameter selection.* Journal of Computational and Graphical Statistics, 34(4), 1397-1409. https://doi.org/10.1080/10618600.2025.2450458
# - Wong, A. P. S., Keeley, R., Carval, T., & the Argo Data Management Team. (2025). *Argo Quality Control Manual for CTD and Trajectory Data* (Version 3.9). https://doi.org/10.13155/33951
# - Yarger, D., Stoev, S., & Hsing, T. (2022). *A functional-data approach to the Argo data.* The Annals of Applied Statistics, 16(1), 216-246. https://doi.org/10.1214/21-AOAS1477
#
# ## Next Steps
#
# Notebook 01 leaves the custom method in a specific place: plausible, working, and worth benchmarking, but not yet justified beyond that.
#
# Immediate follow-on work:
#
# 1. benchmark the method against Akima and PCHIP on the same withheld-point task
# 2. characterize the high-error tail and identify where the custom approach breaks down
# 3. test whether the uncertainty fields remain useful when the fit becomes less accurate
# 4. check whether the method's compactness and queryability survive broader comparisons
#
# Those questions are the bridge to notebook 02.
#
