from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Collection, Iterator, Optional

import numpy as np
import pandas as pd
import xarray as xr
from numpy.typing import ArrayLike

from ..cycle import InterpolationModel, ModelSettings
from ..cycle.adapter.BaseAdapter import BaseAdapter
from ..cycle.domain import ModelData, ModelMeta
from .CycleBatch import CycleBatch
from .CycleIndex import CycleIndex

TimestampLike = datetime | pd.Timestamp | np.datetime64

_ARGO_DATASET_COLUMNS = [
    "PLATFORM_NUMBER",
    "CYCLE_NUMBER",
    "DIRECTION",
    "LATITUDE",
    "LONGITUDE",
    "TIME",
    "PRES",
    "TEMP",
    "PSAL",
]


@dataclass(slots=True)
class CycleCollection:
    models: dict[str, InterpolationModel] = field(repr=False)
    _index: CycleIndex = field(init=False, repr=False)

    @classmethod
    def from_dataset(
        cls,
        dataset: xr.Dataset,
        adapter: type[BaseAdapter],
        settings: ModelSettings,
        min_points: int = 5,
        duplicate_pressure_rule: str = "mean",
    ) -> CycleCollection:
        missing = [name for name in _ARGO_DATASET_COLUMNS if name not in dataset]
        if missing:
            raise ValueError(f"Dataset is missing required variables: {missing}")

        # TODO: Drop only rows missing modeled values, and handle cycle metadata separately.
        data_frame = dataset[_ARGO_DATASET_COLUMNS].to_dataframe().dropna()

        models: dict[str, InterpolationModel] = {}
        group_cols = ["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"]
        for (platform_number, cycle_number, direction), cycle_frame in data_frame.groupby(
            group_cols,
            sort=True,
        ):
            model_data = ModelData(
                pressure=cycle_frame["PRES"].to_numpy(dtype=float),
                temperature=cycle_frame["TEMP"].to_numpy(dtype=float),
                salinity=cycle_frame["PSAL"].to_numpy(dtype=float),
            ).clean_duplicates(rule=duplicate_pressure_rule)

            if len(model_data) < min_points:
                continue

            cycle_frame = cycle_frame.sort_values("PRES", kind="stable")
            model_meta = ModelMeta(
                platform_number=str(platform_number),
                cycle_number=str(cycle_number),
                direction=str(direction),
                latitude=float(cycle_frame["LATITUDE"].iloc[0]),
                longitude=float(cycle_frame["LONGITUDE"].iloc[0]),
                timestamp=pd.Timestamp(cycle_frame["TIME"].iloc[0]).to_datetime64(),
                profile_pressure=(
                    float(model_data.pressure[0]),
                    float(model_data.pressure[-1]),
                ),
            )

            model = InterpolationModel.build(model_meta, model_data, adapter, settings)
            models[model.meta.cycle_id] = model

        return cls(models=models)

    def __post_init__(self) -> None:
        duplicate_ids = [k for k, v in self.models.items() if k != v.meta.cycle_id]
        if duplicate_ids:
            raise ValueError("dict keys must match model.meta.cycle_id")
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        models = list(self.models.values())
        self._index = CycleIndex(
            cycle_id=np.array([model.meta.cycle_id for model in models], dtype=object),
            platform_number=np.array(
                [model.meta.platform_number for model in models],
                dtype=object,
            ),
            cycle_number=np.array([model.meta.cycle_number for model in models], dtype=object),
            direction=np.array([model.meta.direction for model in models], dtype=object),
            latitude=np.array([model.meta.latitude for model in models], dtype=float),
            longitude=np.array([model.meta.longitude for model in models], dtype=float),
            timestamp=np.array(
                [pd.Timestamp(model.meta.timestamp).to_datetime64() for model in models],
                dtype="datetime64[ns]",
            ),
            seasonal_timestamp=np.array(
                [
                    pd.Timestamp(model.meta.timestamp).replace(year=2000).to_datetime64()
                    for model in models
                ],
                dtype="datetime64[ns]",
            ),
            pressure_min=np.array(
                [model.meta.profile_pressure[0] for model in models],
                dtype=float,
            ),
            pressure_max=np.array(
                [model.meta.profile_pressure[1] for model in models],
                dtype=float,
            ),
        )

    def __len__(self) -> int:
        return len(self.models)

    def __iter__(self) -> Iterator[tuple[str, InterpolationModel]]:
        return iter(self.models.items())

    def __getitem__(self, cycle_id: str) -> InterpolationModel:
        return self.models[cycle_id]

    def _normalize_mask(self, mask: ArrayLike) -> np.ndarray:
        normalized_mask = np.asarray(mask, dtype=bool)
        if normalized_mask.ndim != 1:
            raise ValueError("mask must be a one-dimensional boolean array")
        if len(normalized_mask) != len(self._index):
            raise ValueError("mask length must match the number of cycle interpolators")
        return normalized_mask

    def index(self, mask: Optional[np.ndarray] = None) -> CycleIndex:
        if mask is None:
            return self._index
        return self._index.select(self._normalize_mask(mask))

    @property
    def metadata(self) -> pd.DataFrame:
        # TODO: Remove this deprecated convenience property after callers migrate to index().
        warnings.warn((
                "CycleCollection.metadata is deprecated; use "
                "CycleCollection.index().to_frame() instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return self._index.to_frame()

    def mask(
        self,
        lat: Optional[tuple[float, float]] = None,
        lon: Optional[tuple[float, float]] = None,
        timestamp: Optional[tuple[TimestampLike, TimestampLike]] = None,
        cyclical_dates: Optional[tuple[TimestampLike, TimestampLike]] = None,
        exclude_cycle_ids: Optional[Collection[str]] = None,
        exclude_platform_number: Optional[str] = None,
    ) -> np.ndarray:
        metadata = self._index
        mask = np.ones(len(metadata), dtype=bool)

        if lat is not None:
            mask &= (metadata.latitude >= lat[0]) & (metadata.latitude <= lat[1])

        if lon is not None:
            mask &= (metadata.longitude >= lon[0]) & (metadata.longitude <= lon[1])

        if timestamp is not None:
            filter_start = pd.Timestamp(timestamp[0]).to_datetime64()
            filter_end = pd.Timestamp(timestamp[1]).to_datetime64()
            mask &= (metadata.timestamp >= filter_start) & (metadata.timestamp <= filter_end)

        if cyclical_dates is not None:
            filter_norm = tuple(
                pd.Timestamp(filter_date).replace(year=2000).to_datetime64()
                for filter_date in cyclical_dates
            )

            if filter_norm[0] <= filter_norm[1]:
                mask &= (
                    (metadata.seasonal_timestamp >= filter_norm[0])
                    & (metadata.seasonal_timestamp <= filter_norm[1])
                )
            else:
                mask &= (
                    (metadata.seasonal_timestamp >= filter_norm[0])
                    | (metadata.seasonal_timestamp <= filter_norm[1])
                )

        if exclude_platform_number is not None:
            mask &= metadata.platform_number != exclude_platform_number

        if exclude_cycle_ids:
            mask &= ~np.isin(metadata.cycle_id, list(exclude_cycle_ids))

        return mask

    def filter(self,
       lat: Optional[tuple[float, float]] = None,
       lon: Optional[tuple[float, float]] = None,
       timestamp: Optional[tuple[datetime, datetime]] = None,
       cyclical_dates: Optional[tuple[datetime, datetime]] = None,
       exclude_cycle_ids: Optional[Collection[str]] = None,
       exclude_platform_number: Optional[str] = None,
       return_models_dict: bool = False,
    ) -> CycleCollection | dict[str, InterpolationModel]:
        mask = self.mask(
            lat=lat,
            lon=lon,
            timestamp=timestamp,
            cyclical_dates=cyclical_dates,
            exclude_cycle_ids=exclude_cycle_ids,
            exclude_platform_number=exclude_platform_number,
        )
        models = {
            cycle_id: self.models[cycle_id]
            for cycle_id in self._index.cycle_id[mask]
        }

        if return_models_dict:
            return models

        return type(self)(models=models)

    def pop(self, cycle_id: str) -> InterpolationModel:
        model = self.models.pop(cycle_id)
        self._rebuild_index()
        return model

    def _interpolate_cycle_data(
        self,
        pressure_data: ArrayLike,
        method_name: str,
        mask: ArrayLike | None = None,
    ) -> CycleBatch:
        pressure_values = np.asarray(pressure_data, dtype=float)
        pressure_index = pd.Index(pressure_values, name="pressure")

        metadata = self._index if mask is None else self.index(mask)
        cycle_ids = metadata.cycle_id

        if len(cycle_ids) == 0:
            empty_frame = pd.DataFrame(index=pressure_index)
            return CycleBatch(temperature=empty_frame.copy(), salinity=empty_frame.copy())

        temp_data = np.empty((len(pressure_values), len(cycle_ids)), dtype=float)
        sal_data = np.empty((len(pressure_values), len(cycle_ids)), dtype=float)

        for position, cycle_id in enumerate(cycle_ids):
            model_interp = getattr(self.models[cycle_id], method_name)(pressure_values)
            temp_data[:, position] = model_interp.temperature
            sal_data[:, position] = model_interp.salinity

        return CycleBatch(
            temperature=pd.DataFrame(temp_data, index=pressure_index, columns=cycle_ids),
            salinity=pd.DataFrame(sal_data, index=pressure_index, columns=cycle_ids),
        )

    def interpolate(self, pressure_data: ArrayLike, *, mask: ArrayLike | None = None) -> CycleBatch:
        return self._interpolate_cycle_data(pressure_data, "interpolate", mask=mask)

    def interp_error(
        self,
        pressure_data: ArrayLike,
        *,
        mask: ArrayLike | None = None,
    ) -> CycleBatch:
        return self._interpolate_cycle_data(pressure_data, "interp_error", mask=mask)
