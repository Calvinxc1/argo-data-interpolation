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
# # 02. Argo Cycle Representation Validation
#
# Notebook 01 asked whether the custom spline method worked at all as a compact and uncertainty-aware profile representation. Notebook 02 asks the next question: how does that same custom method compare to more traditional exact-interpolant baselines on the same withheld-point reconstruction task?
#
# The goal here is to separate reconstruction accuracy from artifact compactness and stability, and to see whether the method-confirmation story from notebook 01 survives an apples-to-apples comparison. The baseline families map onto the interpolation literature summarized in the topic review: Akima as a local piecewise-cubic exact interpolant (Akima, 1970, pp. 2-5) and PCHIP-type methods as the shape-preserving family emphasized in the Argo interpolation literature (Barker & McDougall, 2020, pp. 1-2, 4-7, 14-15).
#
# This notebook should be read alongside the topic notes:
#
# - [Method Comparison Notes](../notes/method-comparison-notes.md)
# - [Experiment Design Notes](../notes/experiment-design-notes.md)
# - [Framing Notes](../notes/framing-notes.md)
#
#

# %%
import numpy as np
from argopy import DataFetcher as ArgoDataFetcher
import pandas as pd
from tqdm.auto import tqdm
from scipy.interpolate import Akima1DInterpolator, PchipInterpolator
import pickle
from pympler import asizeof
from pathlib import Path

# %%
from lib import ModelError, SensorError, CycleError, CycleModel, CycleSettings
from lib import build_model, calc_fold_error
from lib.calc_rmse import calc_rmse

from argo_interp.data import get_data


# %% [markdown]
# ## Benchmark Setup
#
# The next cells define the shared fold logic, baseline comparison helpers, and sampled profile set used throughout the notebook. The Akima and PCHIP helper functions are kept intentionally close to the spline validation pattern so that the comparison reflects representation differences rather than different split logic.
#
# That keeps the benchmark focused on one narrow question already motivated by the literature: what happens when an exact interpolant and a compact stored representation are asked to solve the same within-profile reconstruction problem (Akima, 1970, pp. 2-5; Barker & McDougall, 2020, pp. 1-2, 4-7; Yarger et al., 2022, pp. 11-12, 216-218)?
#
#

# %%
def interleaved_fold_index(cycle_data: pd.DataFrame, folds: int) -> np.ndarray:
    """Match calc_fold_error() interleaved validation fold assignment exactly."""
    fold_obs_idx = np.arange(1, len(cycle_data) - 1)
    return np.array([-1, *((fold_obs_idx - 1) % folds), -1])


# %%
def akima_kfold(cycle_data, folds=5):
    cycle_data = cycle_data.sort_values('PRES').reset_index(drop=True)
    folds_idx = interleaved_fold_index(cycle_data, folds)

    valid_obs = 0
    temp_rmse = 0
    sal_rmse = 0
    for fold in range(folds):
        valid_mask = folds_idx == fold
        train_data = cycle_data.loc[~valid_mask]
        valid_data = cycle_data.loc[valid_mask]

        temp_model = Akima1DInterpolator(x=train_data['PRES'], y=train_data['TEMP'], method='akima')
        temp_predicts = temp_model(valid_data['PRES'])
        temp_rmse += calc_rmse(valid_data['TEMP'], temp_predicts) * len(valid_data)

        sal_model = Akima1DInterpolator(x=train_data['PRES'], y=train_data['PSAL'], method='akima')
        sal_predicts = sal_model(valid_data['PRES'])
        sal_rmse += calc_rmse(valid_data['PSAL'], sal_predicts) * len(valid_data)

        valid_obs += len(valid_data)
    temp_rmse /= valid_obs
    sal_rmse /= valid_obs
    return temp_rmse, sal_rmse



# %%
def pchip_kfold(cycle_data, folds=5):
    cycle_data = cycle_data.sort_values('PRES').reset_index(drop=True)
    folds_idx = interleaved_fold_index(cycle_data, folds)

    valid_obs = 0
    temp_rmse = 0
    sal_rmse = 0
    for fold in range(folds):
        valid_mask = folds_idx == fold
        train_data = cycle_data.loc[~valid_mask]
        valid_data = cycle_data.loc[valid_mask]

        temp_model = PchipInterpolator(x=train_data['PRES'], y=train_data['TEMP'])
        temp_predicts = temp_model(valid_data['PRES'])
        temp_rmse += calc_rmse(valid_data['TEMP'], temp_predicts) * len(valid_data)

        sal_model = PchipInterpolator(x=train_data['PRES'], y=train_data['PSAL'])
        sal_predicts = sal_model(valid_data['PRES'])
        sal_rmse += calc_rmse(valid_data['PSAL'], sal_predicts) * len(valid_data)

        valid_obs += len(valid_data)
    temp_rmse /= valid_obs
    sal_rmse /= valid_obs
    return temp_rmse, sal_rmse



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
# ## Evaluation Scope and Interpretation Guardrails
#
# This notebook compares three profile representations on the same interleaved k-fold omitted-point reconstruction task:
#
# - the current compact spline artifact,
# - `Akima1DInterpolator`, and
# - `PchipInterpolator`.
#
# The fold assignment is intentionally matched to `calc_fold_error()` so the benchmark stays aligned with the custom spline pipeline from notebook 01. That makes this a fair test of one narrow question: how well does each method reconstruct omitted observed depths within a profile? In the reviewed literature, Akima and PCHIP-type methods belong to the exact-interpolation side of the problem, while Yarger et al. (2022, pp. 11-12, 216-218) treat continuous vertical representation as a distinct functional-data step.
#
# This notebook should be interpreted alongside the topic notes rather than as a standalone framing document:
#
# - [Method Comparison Notes](../notes/method-comparison-notes.md): exact interpolants and compact representations solve different objectives.
# - [Experiment Design Notes](../notes/experiment-design-notes.md): Akima and PCHIP are the practical Python baselines for this benchmark.
# - [Framing Notes](../notes/framing-notes.md): the intended project framing is a compact, uncertainty-aware profile representation layer rather than a claim of best interpolation RMSE.
#
# In practical terms, this notebook can speak directly to omitted-point RMSE, artifact footprint, and footprint stability. It cannot by itself establish downstream acoustic utility, operational value of the uncertainty terms, or superiority as a prior layer once sparse local sensing is introduced. It also does not yet answer whether the custom spline machinery is the right non-exact spline family to carry forward; notebook 03 takes up that question directly.
#
#

# %% [markdown]
# ## Compact Spline Artifact Results
#
# The next cells fit the current spline-based cycle artifact across the sampled profiles and summarize its reconstruction error and artifact footprint.
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
    cycle_data = cycle_data.sort_values('PRES').reset_index(drop=True)
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

# %%
model_error = pd.DataFrame([model.error.model for model in cycle_models.values()])
pd.concat([
    model_error.mean().rename('mean'),
    model_error.median().rename('median'),
    model_error.std().rename('stdev'),
], axis=1)

# %%
model_sizes = pd.DataFrame({cycle_num: {
    'memory': asizeof.asizeof(model),
    'file': len(pickle.dumps(model)),
} for cycle_num, model in cycle_models.items()}).T
pd.concat([
    model_sizes.mean().rename('mean'),
    model_sizes.median().rename('median'),
    model_sizes.std().rename('stdev'),
], axis=1)

# %% [markdown]
# ### Spline Artifact Measurement Scope
#
# The spline result here is measured as a fuller deployable artifact, not just a bare interpolator object.
#
# `SplineModel` includes:
#
# - a temperature spline,
# - a salinity spline,
# - model-error metadata,
# - sensor-error metadata,
# - `SplineSettings`, and
# - pressure bounds.
#
# So the memory and pickle-size numbers for this method reflect a richer artifact definition than a raw interpolator alone. That matters for interpretation: if the fuller spline artifact still remains smaller than the exact-interpolant baselines, the compactness result is conservative rather than inflated.
#
#

# %% [markdown]
# ## Akima Baseline Results
#
# The next cells evaluate `Akima1DInterpolator` under the same interleaved omitted-point validation logic and summarize both reconstruction error and interpolator footprint.
#
#

# %%
akima_model_errors = {}
akima_model_sizes = {}
for cycle_number, cycle_data in tqdm(readings.groupby('PLATFORM_CYCLE')):
    cycle_data = cycle_data.sort_values('PRES').reset_index(drop=True)
    temp_rmse, sal_rmse = akima_kfold(cycle_data, folds=5)

    temp_model = Akima1DInterpolator(x=cycle_data['PRES'], y=cycle_data['TEMP'], method='akima')
    sal_model = Akima1DInterpolator(x=cycle_data['PRES'], y=cycle_data['PSAL'], method='akima')

    akima_model_errors[cycle_number] = {'temp': temp_rmse, 'sal': sal_rmse}
    akima_model_sizes[cycle_number] = {'temp_memory': asizeof.asizeof(temp_model), 'temp_file': len(pickle.dumps(temp_model)),
                                       'sal_memory': asizeof.asizeof(sal_model), 'sal_file': len(pickle.dumps(sal_model))}
akima_model_errors = pd.DataFrame(akima_model_errors).T
akima_model_sizes = pd.DataFrame(akima_model_sizes).T

# %%
akima_model_errors.mean()

# %%
akima_model_sizes['memory'] = akima_model_sizes['temp_memory'] + akima_model_sizes['sal_memory']
akima_model_sizes['file'] = akima_model_sizes['temp_file'] + akima_model_sizes['sal_file']
pd.concat([
    akima_model_sizes.mean().rename('mean'),
    akima_model_sizes.median().rename('median'),
    akima_model_sizes.std().rename('stdev'),
], axis=1).loc[['memory', 'file']]

# %%
akima_model_sizes.loc[akima_model_sizes['memory'] < np.nanpercentile(akima_model_sizes['memory'], 90), 'memory'].std()

# %%
akima_model_sizes.loc[akima_model_sizes['file'] < np.nanpercentile(akima_model_sizes['file'], 90), 'file'].std()

# %%
# cycle_number = np.random.choice(list(cycle_models.keys()))
cycle_number = '6900551-71'
print(f"Cycle #: {cycle_number}")
cycle_data = readings.loc[readings['PLATFORM_CYCLE'] == cycle_number]

# %% [markdown]
# ## PCHIP Baseline Results
#
# The next cells evaluate `PchipInterpolator` under the same omitted-point validation logic. In practice, this serves as a second strong exact-interpolant comparator and helps show whether the footprint pattern is specific to Akima or characteristic of exact interpolants more generally.
#
#

# %%
pchip_model_errors = {}
pchip_model_sizes = {}
for cycle_number, cycle_data in tqdm(readings.groupby('PLATFORM_CYCLE')):
    cycle_data = cycle_data.sort_values('PRES').reset_index(drop=True)
    temp_rmse, sal_rmse = pchip_kfold(cycle_data, folds=5)

    temp_model = PchipInterpolator(x=cycle_data['PRES'], y=cycle_data['TEMP'])
    sal_model = PchipInterpolator(x=cycle_data['PRES'], y=cycle_data['PSAL'])

    pchip_model_errors[cycle_number] = {'temp': temp_rmse, 'sal': sal_rmse}
    pchip_model_sizes[cycle_number] = {'temp_memory': asizeof.asizeof(temp_model), 'temp_file': len(pickle.dumps(temp_model)),
                                       'sal_memory': asizeof.asizeof(sal_model), 'sal_file': len(pickle.dumps(sal_model))}
pchip_model_errors = pd.DataFrame(pchip_model_errors).T
pchip_model_sizes = pd.DataFrame(pchip_model_sizes).T

# %%
pchip_model_errors.mean()

# %%
pchip_model_sizes['memory'] = pchip_model_sizes['temp_memory'] + pchip_model_sizes['sal_memory']
pchip_model_sizes['file'] = pchip_model_sizes['temp_file'] + pchip_model_sizes['sal_file']
pd.concat([
    pchip_model_sizes.mean().rename('mean'),
    pchip_model_sizes.median().rename('median'),
    pchip_model_sizes.std().rename('stdev'),
], axis=1).loc[['memory', 'file']]

# %%
pchip_model_sizes.loc[pchip_model_sizes['memory'] < np.nanpercentile(pchip_model_sizes['memory'], 90), 'memory'].std()

# %%
pchip_model_sizes.loc[pchip_model_sizes['file'] < np.nanpercentile(pchip_model_sizes['file'], 90), 'file'].std()

# %% [markdown]
# ## Comparative Interpretation
#
# At the current settings, Akima and PCHIP behave very similarly on both omitted-point RMSE and interpolator footprint. The central comparison is therefore not Akima versus PCHIP, but exact interpolants versus the custom compact spline artifact introduced in notebook 01.
#
# ### Empirical Takeaways
#
# - Exact interpolants win clearly on omitted-point reconstruction RMSE.
# - The compact spline artifact remains materially smaller in both memory and serialized size.
# - The spline artifact also appears much more stable in footprint across profiles, while Akima/PCHIP show much heavier right-tail behavior.
#
# ### Footprint Stability Summary
#
# **Memory footprint**
#
# | Method | Mean | Median | Stdev | Stdev (<P90) |
# | --- | ---: | ---: | ---: | ---: |
# | Spline artifact | 2778.71 | 2776.00 | 99.78 | - |
# | Akima | 9058.93 | 6800.00 | 8723.07 | 420.12 |
# | PCHIP | 9058.93 | 6800.00 | 8723.07 | 420.12 |
#
# **Serialized file footprint**
#
# | Method | Mean | Median | Stdev | Stdev (<P90) |
# | --- | ---: | ---: | ---: | ---: |
# | Spline artifact | 945.81 | 944.00 | 66.52 | - |
# | Akima | 8750.54 | 6492.00 | 8724.32 | 420.88 |
# | PCHIP | 8746.54 | 6488.00 | 8724.32 | 420.88 |
#
# The means show how strongly the exact-interpolant baselines are influenced by a heavy right tail. The medians give the more typical picture: the compact spline artifact is still about 2.5x smaller in memory footprint and roughly 6.5x smaller in serialized size than Akima/PCHIP.
#
# The standard-deviation pattern points the same way. Trimming the top 10% of exact-interpolant sizes collapses the Akima/PCHIP spread dramatically, but it does not remove the stability gap. Even after trimming, the exact-interpolant memory-footprint stdev remains about 4.2x the spline artifact, and the file-footprint stdev remains about 6.3x the spline artifact. That suggests the spline artifact's tighter footprint is not just a consequence of a few outliers in Akima/PCHIP; it reflects a genuinely more predictable artifact size distribution.
#
# ### Implementation-State Interpretation
#
# The SciPy baselines are relatively lean interpolator objects. At the source level, both `Akima1DInterpolator` and `PchipInterpolator` are piecewise-cubic interpolator classes that store breakpoint and coefficient state for each interval. In practice they behave very similarly in both RMSE and footprint in this notebook.
#
# The current spline implementation stores a different kind of state:
#
# - a compressed spline basis (`t`, `c`, `k`) for each variable,
# - then wraps those splines in `SplineModel` with error metadata, settings, and bounds.
#
# That wrapper layer is now a relatively small share of the total artifact footprint. In the current implementation-level breakdown, the wrapper and attached metadata account for only about 8% of in-memory footprint and roughly 15-20% of serialized footprint. Using that as a rough adjustment, a more direct model-only comparison would put the spline representation at about 2550 mean / 2552 median for memory and roughly 790-840 mean / 790-840 median for serialized size, depending on whether the file-size adjustment is treated proportionally or as an approximately fixed metadata slice. On that rough basis, the spline representation would still be about 3.5x smaller than Akima/PCHIP on mean memory footprint, about 2.7x smaller on median memory footprint, about 10.4x-11.1x smaller on mean serialized size, and about 7.7x-8.2x smaller on median serialized size.
#
# So the exact-interpolant baselines are not secretly carrying large wrapper structures that would explain away the footprint result. The more compact and more stable footprint of the spline artifact appears to come from the representation itself, not from a measurement artifact.
#
# ### Bottom Line for This Experiment
#
# This notebook supports a narrower but coherent conclusion:
#
# - the current spline pipeline is **not** the strongest pure interpolation method under this validation task,
# - but it does appear to offer a substantially smaller and more predictable artifact,
# - so notebook 01's feasibility result survives comparison as a real tradeoff rather than collapsing immediately,
# - and the next question becomes whether this custom spline implementation actually earns its complexity relative to simpler spline-family alternatives.
#
#

# %% [markdown]
# ## Framing References
#
# - Akima, H. (1970). *A new method of interpolation and smooth curve fitting based on local procedures.* Journal of the ACM, 17(4), 589-602. https://doi.org/10.1145/321607.321609
# - Barker, P. M., & McDougall, T. J. (2020). *Two interpolation methods using multiply-rotated piecewise cubic Hermite interpolating polynomials.* Journal of Atmospheric and Oceanic Technology, 37(4), 605-619. https://doi.org/10.1175/JTECH-D-19-0211.1
# - Yarger, D., Stoev, S., & Hsing, T. (2022). *A functional-data approach to the Argo data.* The Annals of Applied Statistics, 16(1), 216-246. https://doi.org/10.1214/21-AOAS1477
#
# These references are the main framing support for the method-class distinctions cited in this notebook. For broader topic context and the canonical source-backed synthesis, see [../literature-review.md](../literature-review.md).
#
