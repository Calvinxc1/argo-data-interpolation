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
# # 03. Cycle Representation Comparisons
#
# Notebook 02 established the tradeoff: the custom spline artifact is meaningfully smaller than exact interpolants, but weaker on withheld-point RMSE. Notebook 03 asks whether that tradeoff actually requires the custom curvature-adaptive implementation, or whether simpler traditional / native spline options already cover the same ground more convincingly.
#
# The comparison here is therefore reduced to the core model families that still matter: linear interpolation, PCHIP, and SciPy's native spline path. Those choices match the method classes emphasized in the topic literature review: linear interpolation as the simplest baseline, shape-preserving PCHIP-type methods as the main Argo interpolation comparator, and continuous spline representations as the natural family for compact functional encoding (Li et al., 2022, pp. 1, 8; Barker & McDougall, 2020, pp. 1-2, 4-7, 14-15; Yarger et al., 2022, pp. 11-12, 216-218).

# %% [markdown]
# ## Scope and Research Role
#
# This notebook should be read as the decision notebook in the sequence rather than as another method-introduction notebook.
#
# - The comparison is intended to sit directly after notebook 02, using the same general cycle-level logic in a simpler model space.
# - The main purpose is to test whether the custom spline path was buying anything that SciPy's native spline implementation does not already provide.
# - The broader project takeaway is expected to be about uncertainty-aware compact representation, not about inventing a new spline family. That emphasis is consistent with the Argo QC/error context and with Yarger et al.'s framing of vertical profile representation as part of a larger inferential workflow rather than as interpolation alone (Wong et al., 2025, pp. 43, 47, 50, 55-56, 84; Yarger et al., 2022, pp. 11-12, 216-218).
#
# So the central interpretive questions are:
#
# 1. Does the native spline path dominate the custom spline direction on simplicity and performance?
# 2. Does PCHIP still sit on the low-RMSE end of the tradeoff?
# 3. If spline methods are weaker on RMSE, do they still earn their place through tunability and smaller artifacts?

# %%
import pickle

import numpy as np
import pandas as pd
from pympler import asizeof
from tqdm.auto import tqdm

# %%
from argo_interp.data import get_data

from argo_interp.cycle.adapter import LinearAdapter, PchipAdapter, SplineAdapter
from argo_interp.cycle.config import ModelKwargs, ModelSettings, SensorAccuracy
from argo_interp.cycle.domain import ModelData, ModelMeta
from argo_interp.cycle.model import Model

# %% [markdown]
# ## Local Assumptions
#
# The sensor terms below are fixed local defaults passed into `ModelSettings`. Those values come from the delayed-mode Argo uncertainty conventions summarized in the topic literature review: 2.4 dbar for pressure, 0.002°C for temperature, and a 0.01 PSU floor for salinity in the standard float setting (Wong et al., 2025, pp. 43, 47, 50, 55-56, 84). That is acceptable for the present purpose because this notebook is not trying to calibrate uncertainty intervals; it is trying to locate a sensible model family to carry forward into the uncertainty-aware representation work.
#
# In other words, this notebook helps decide what is worth quantifying uncertainty around, not how that uncertainty should ultimately be calibrated.

# %%
SENSOR_ACCURACY = {
    'pressure': 2.4,
    'temperature': 0.002,
    'salinity': 0.01,
}

# %% [markdown]
# ## Data Pull
#
# This uses the same 2011 regional cycle sample as notebook 02 so the comparison stays tied to the validation dataset rather than drifting to a different slice. The sample is still compact enough to compare the core model classes on many individual cycles without turning the notebook into a large batch benchmark.
#
# The important thing here is relative behavior across models on the same loop, not publishing these particular aggregate numbers as final topic results.

# %%
box = [
    -75, -45,  # Longitude min/max
    20, 30,    # Latitude min/max
    0, 3000,   # Pressure/depth min/max
    '2011-01', '2011-06',
]
ds = get_data(box)

# %% [markdown]
# ## Model Setup
#
# The comparison uses four states:
#
# - `LinearAdapter`: minimal exact-interpolation baseline
# - `PchipAdapter`: shape-preserving exact-interpolation baseline
# - `SplineAdapter` with default settings: native SciPy spline path without additional smoothing
# - `SplineAdapter` with heuristic `s`: the same native spline family, but with explicit smoothing used as a footprint / fidelity control
#
# This is the key shift from notebooks 01 and 02. Linear interpolation and PCHIP-type methods are the most relevant exact baselines from the reviewed oceanographic literature, while spline smoothing connects more naturally to the continuous-representation direction described by Yarger et al. (2022, pp. 11-12, 216-218) (Li et al., 2022, pp. 1, 8; Barker & McDougall, 2020, pp. 1-2, 4-7). The question is no longer whether the custom spline can be made to work; notebooks 01 and 02 already answered that. The question is whether the native spline family already captures the only part of that story that remains compelling.

# %%
settings = ModelSettings(
    n_folds=5,
    sensor_accuracy=SensorAccuracy(**SENSOR_ACCURACY),
)

# %%
def build_smooth_settings(
    ref_temp_error: float,
    ref_sal_error: float,
    model_data: ModelData,
    settings: ModelSettings,
    smooth_scaler: float = 0.1,
) -> ModelSettings:
    """Create a smoothing-spline settings variant from reference fold errors."""
    temp_smooth_param = (ref_temp_error ** 2) * model_data.n_obs * smooth_scaler
    sal_smooth_param = (ref_sal_error ** 2) * model_data.n_obs * smooth_scaler
    return ModelSettings(
        n_folds=settings.n_folds,
        model_kwargs=ModelKwargs(
            temperature={**settings.model_kwargs.temperature, 's': temp_smooth_param},
            salinity={**settings.model_kwargs.salinity, 's': sal_smooth_param},
        ),
        sensor_accuracy=settings.sensor_accuracy,
    )

# %% [markdown]
# ## Cycle Loop
#
# For each cycle, the notebook constructs the current package metadata, collapses duplicate pressures, builds each model variant, and records two output families:
#
# - omitted-point model error from the package fold logic
# - artifact footprint in memory and serialized form
#
# That split matters because this notebook is trying to settle the custom-method question. If PCHIP wins on RMSE but native spline methods can be tuned into substantially smaller artifacts, then the custom spline story loses most of its remaining rationale and the broader spline story becomes one of controlled approximation and later uncertainty quantification.

# %%
model_errors = {}

cycles = len(ds[['PLATFORM_NUMBER', 'CYCLE_NUMBER', 'DIRECTION']].to_dataframe().drop_duplicates())
for (platform_number, cycle_number, direction), cycle_ds in tqdm(
    ds.groupby(['PLATFORM_NUMBER', 'CYCLE_NUMBER', 'DIRECTION']),
    total=cycles,
):
    cycle_id = f"{int(platform_number)}|{int(cycle_number)}-{direction}"
    cycle_ds = cycle_ds.sortby('PRES')

    model_meta = ModelMeta(
        cycle_id=cycle_id,
        latitude=float(cycle_ds['LATITUDE'].values[0]),
        longitude=float(cycle_ds['LONGITUDE'].values[0]),
        timestamp=cycle_ds['TIME'].values[0],
        profile_pressure=(
            float(cycle_ds['PRES'].min().item()),
            float(cycle_ds['PRES'].max().item()),
        ),
    )

    # Fitting requires strictly increasing pressures, so duplicate levels are collapsed first.
    model_data = ModelData(
        pressure=cycle_ds['PRES'].values,
        temperature=cycle_ds['TEMP'].values,
        salinity=cycle_ds['PSAL'].values,
    ).clean_duplicates(rule='mean')

    linear_model = Model.build(model_meta, model_data, LinearAdapter, settings)
    pchip_model = Model.build(model_meta, model_data, PchipAdapter, settings)
    spline_model = Model.build(model_meta, model_data, SplineAdapter, settings)

    # The smoothed spline keeps the same native spline family but exposes an explicit tradeoff knob.
    smooth_settings = build_smooth_settings(
        spline_model.error.temperature.model,
        spline_model.error.salinity.model,
        model_data,
        settings,
        smooth_scaler=5e-2,
    )
    smooth_spline_model = Model.build(model_meta, model_data, SplineAdapter, smooth_settings)

    model_errors[cycle_id] = {
        'temp_linear': linear_model.error.temperature.model,
        'temp_pchip': pchip_model.error.temperature.model,
        'temp_spline': spline_model.error.temperature.model,
        'temp_smooth_spline': smooth_spline_model.error.temperature.model,
        'sal_linear': linear_model.error.salinity.model,
        'sal_pchip': pchip_model.error.salinity.model,
        'sal_spline': spline_model.error.salinity.model,
        'sal_smooth_spline': smooth_spline_model.error.salinity.model,
        'memory_linear': asizeof.asizeof(linear_model),
        'memory_pchip': asizeof.asizeof(pchip_model),
        'memory_spline': asizeof.asizeof(spline_model),
        'memory_smooth_spline': asizeof.asizeof(smooth_spline_model),
        'file_linear': len(pickle.dumps(linear_model)),
        'file_pchip': len(pickle.dumps(pchip_model)),
        'file_spline': len(pickle.dumps(spline_model)),
        'file_smooth_spline': len(pickle.dumps(smooth_spline_model)),
    }

model_errors = pd.DataFrame(model_errors).T

# %% [markdown]
# ## Summary Table
#
# The table below is the main output of this notebook. Read it as a tradeoff table, not a leaderboard.
#
# - Lower `temp_*` and `sal_*` values mean better omitted-point reconstruction.
# - Lower `memory_*` and `file_*` values mean a smaller stored artifact.
# - The practical interpretation is whether accepting weaker RMSE than PCHIP buys enough compactness and tunability to justify carrying the spline family forward into the uncertainty-aware representation work.

# %%
pd.concat([
    model_errors.mean().rename('mean'),
    model_errors.median().rename('median'),
    model_errors.std().rename('stdev'),
], axis=1)

# %% [markdown]
# ## Exploratory Conclusion
#
# This notebook is the point where the sequence makes its decision:
#
# - the old custom spline direction is not compelling as a standalone technique if SciPy's native spline implementation already captures the same part of the tradeoff more simply,
# - PCHIP remains the stronger choice when the target is pure reconstruction RMSE,
# - spline methods remain interesting because the `s` parameter gives a direct handle on fidelity versus footprint,
# - that makes the spline family relevant as a compact, tunable representation layer whose next research step is uncertainty quantification, not further technique invention.
#
# In other words, notebook 03 closes the loop opened by notebooks 01 and 02. The custom spline was a useful exploratory method, but the more durable research direction is the simpler native spline family plus explicit uncertainty work.

# %% [markdown]
# ## Framing References
#
# - Barker, P. M., & McDougall, T. J. (2020). *Two interpolation methods using multiply-rotated piecewise cubic Hermite interpolating polynomials.* Journal of Atmospheric and Oceanic Technology, 37(4), 605-619. https://doi.org/10.1175/JTECH-D-19-0211.1
# - Li, Y., Church, J. A., McDougall, T. J., & Barker, P. M. (2022). *Sensitivity of observationally based estimates of ocean heat content and thermal expansion to vertical interpolation schemes.* Geophysical Research Letters, 49(24), e2022GL101079. https://doi.org/10.1029/2022GL101079
# - Wong, A. P. S., Keeley, R., Carval, T., and the Argo Data Management Team (2025). *Argo Quality Control Manual for CTD and Trajectory Data.* Version 3.9. https://doi.org/10.13155/33951
# - Yarger, D., Stoev, S., & Hsing, T. (2022). *A functional-data approach to the Argo data.* The Annals of Applied Statistics, 16(1), 216-246. https://doi.org/10.1214/21-AOAS1477
#
# These references support the model-family framing used here: linear interpolation as a baseline, PCHIP-type methods as the shape-preserving comparator, Argo delayed-mode uncertainty conventions for the fixed sensor terms, and functional spline representation as the broader vertical-encoding context. For the canonical topic synthesis, see [../literature-review.md](../literature-review.md).
