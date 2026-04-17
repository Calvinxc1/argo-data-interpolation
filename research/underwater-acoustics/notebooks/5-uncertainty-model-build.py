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

# %%
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from datetime import timedelta as td
import gsw
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm.auto import tqdm
import scipy.stats as stats
from numpy.typing import ArrayLike

# %%
from argo_interp.data import data_filter, get_data
from argo_interp.cycle.adapter import PchipAdapter
from argo_interp.cycle.config import ModelKwargs, ModelSettings
from argo_interp.cycle.domain import ModelData, ModelMeta
from argo_interp.cycle.model import Model
from argo_interp.model import CycleModels

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

# %%
settings = ModelSettings(
    n_folds=5,
    model_kwargs=ModelKwargs(
        temperature=dict(extrapolate=True),
        salinity=dict(extrapolate=True),
    ),
)

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
cycle_index = cycle_models.index
cycle_ids = cycle_index.index.to_numpy()
platform_numbers = cycle_index["platform_number"].to_numpy()
latitudes = cycle_index["latitude"].to_numpy(dtype=float, copy=False)
longitudes = cycle_index["longitude"].to_numpy(dtype=float, copy=False)
timestamps = pd.to_datetime(cycle_index["timestamp"])
seasonal_timestamps = timestamps.map(lambda x: x.replace(year=2000))

# %%
dist_rad = 1
dist_border_stdev = 3

year_stdev = 3

season_weeks = 8
season_week_stdev = 3


# %%
def weight(x: ArrayLike | float, stdev: ArrayLike | float) -> ArrayLike | float:
    numer = -(x ** 2)
    denom = 2 * (stdev ** 2)
    weight = np.exp(numer / denom)
    return weight


# %%
@dataclass(frozen=True, slots=True)
class WeightScale:
    stdev: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.stdev) or self.stdev <= 0:
            raise ValueError("stdev must be a finite positive float")

    @classmethod
    def from_border(cls, border: float, z: float) -> "GaussianWeightScale":
        if not np.isfinite(border) or border <= 0:
            raise ValueError("border must be a finite positive float")
        if not np.isfinite(z) or z <= 0:
            raise ValueError("z_score must be a finite positive float")

        return cls(stdev=border / z)

    @property
    def variance(self) -> float:
        return self.stdev ** 2

    def weight(self, x: ArrayLike | float) -> ArrayLike | float:
        numer = -(x ** 2)
        denom = 2 * self.variance
        return np.exp(numer / denom)


# %%
def seasonal_window_mask(
    target_timestamp: pd.Timestamp,
    normalized_timestamps: pd.Series,
    seasonal_window_weeks: int,
) -> np.ndarray:
    seasonal_start = (target_timestamp - td(weeks=seasonal_window_weeks)).replace(year=2000)
    seasonal_end = (target_timestamp + td(weeks=seasonal_window_weeks)).replace(year=2000)

    if seasonal_start <= seasonal_end:
        return ((normalized_timestamps >= seasonal_start) & (normalized_timestamps <= seasonal_end)).to_numpy()

    return ((normalized_timestamps >= seasonal_start) | (normalized_timestamps <= seasonal_end)).to_numpy()


# %%
def calc_weight(
    target_position: int,
    candidate_positions: np.ndarray,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    timestamps: pd.Series,
    seasonal_timestamps: pd.Series,
    dist_rad: float,
    dist_border_stdev: float,
    year_stdev: float,
    season_weeks: int,
    season_week_stdev: float,
) -> np.ndarray:
    if len(candidate_positions) == 0:
        return np.array([], dtype=float)

    dist_deg = np.sqrt(
        np.square(latitudes[candidate_positions] - latitudes[target_position])
        + np.square(longitudes[candidate_positions] - longitudes[target_position])
    )
    dist_stdev = dist_rad / dist_border_stdev
    dist_weight = weight(dist_deg, dist_stdev)
    dist_weight /= dist_weight.sum()

    seconds_delta = (
        timestamps.iloc[candidate_positions].to_numpy() - timestamps.iloc[target_position]
    ) / np.timedelta64(1, "s")
    time_stdev = year_stdev * (365.25 * 24 * 60 * 60)
    time_weight = weight(seconds_delta, time_stdev)
    time_weight /= time_weight.sum()

    season_seconds_delta = (
        seasonal_timestamps.iloc[candidate_positions].to_numpy() - seasonal_timestamps.iloc[target_position]
    ) / np.timedelta64(1, "s")
    season_stdev = (season_weeks / season_week_stdev) * (7 * 24 * 60 * 60)
    season_weight = weight(season_seconds_delta, season_stdev)
    season_weight /= season_weight.sum()

    total_weight = dist_weight * time_weight * season_weight
    total_weight /= total_weight.sum()
    return total_weight


# %%
def interpolate_candidate_models(
    candidate_cycle_ids: np.ndarray,
    pressure: np.ndarray,
    model_lookup: dict[str, Model],
) -> tuple[np.ndarray, np.ndarray]:
    interpolated_temperature = np.empty((len(pressure), len(candidate_cycle_ids)), dtype=float)
    interpolated_salinity = np.empty((len(pressure), len(candidate_cycle_ids)), dtype=float)

    for idx, candidate_cycle_id in enumerate(candidate_cycle_ids):
        interp_data = model_lookup[candidate_cycle_id].interpolate(pressure)
        interpolated_temperature[:, idx] = interp_data.temperature
        interpolated_salinity[:, idx] = interp_data.salinity

    return interpolated_temperature, interpolated_salinity


# %%
temp_errors = []
sal_errors = []
for cycle_position, cycle_id in enumerate(tqdm(cycle_ids)):
    model_data = models_data[cycle_id]
    candidate_mask = (
        (np.abs(latitudes - latitudes[cycle_position]) <= dist_rad)
        & (np.abs(longitudes - longitudes[cycle_position]) <= dist_rad)
        & (platform_numbers != platform_numbers[cycle_position])
        & seasonal_window_mask(timestamps.iloc[cycle_position], seasonal_timestamps, season_weeks)
    )
    candidate_positions = np.flatnonzero(candidate_mask)
    candidate_cycle_ids = cycle_ids[candidate_positions]

    if len(candidate_cycle_ids) == 0:
        temp_errors.append(pd.Series(np.nan, index=model_data.pressure, name=cycle_id))
        sal_errors.append(pd.Series(np.nan, index=model_data.pressure, name=cycle_id))
        continue

    total_weight = calc_weight(
        target_position=cycle_position,
        candidate_positions=candidate_positions,
        latitudes=latitudes,
        longitudes=longitudes,
        timestamps=timestamps,
        seasonal_timestamps=seasonal_timestamps,
        dist_rad=dist_rad,
        dist_border_stdev=dist_border_stdev,
        year_stdev=year_stdev,
        season_weeks=season_weeks,
        season_week_stdev=season_week_stdev,
    )

    interp_temperature, interp_salinity = interpolate_candidate_models(
        candidate_cycle_ids=candidate_cycle_ids,
        pressure=model_data.pressure,
        model_lookup=models,
    )

    temp_weight_sum = np.isfinite(interp_temperature) @ total_weight
    sal_weight_sum = np.isfinite(interp_salinity) @ total_weight
    summed_temp = np.nansum(interp_temperature * total_weight, axis=1)
    summed_sal = np.nansum(interp_salinity * total_weight, axis=1)

    predict_temp = pd.Series(
        np.divide(
            summed_temp,
            temp_weight_sum,
            out=np.full(model_data.n_obs, np.nan, dtype=float),
            where=temp_weight_sum > 0,
        ),
        index=model_data.pressure,
        name="temperature",
    )
    predict_sal = pd.Series(
        np.divide(
            summed_sal,
            sal_weight_sum,
            out=np.full(model_data.n_obs, np.nan, dtype=float),
            where=sal_weight_sum > 0,
        ),
        index=model_data.pressure,
        name="salinity",
    )

    temp_errors.append(pd.Series(model_data.temperature, index=model_data.pressure, name=cycle_id) - predict_temp)
    sal_errors.append(pd.Series(model_data.salinity, index=model_data.pressure, name=cycle_id) - predict_sal)

# %%
temp_errors = pd.concat(temp_errors, axis=1)
sal_errors = pd.concat(sal_errors, axis=1)

# %%
