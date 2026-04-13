from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field
from typing import Iterator, Optional
from numpy.typing import ArrayLike
from datetime import datetime

from .CycleData import CycleData
from ..cycle.model import Model


@dataclass(slots=True)
class CycleModels:
    models: dict[str, Model] = field(repr=False)
    _meta_index: pd.DataFrame = field(init=False, repr=False)

    def __post_init__(self) -> None:
        duplicate_ids = [k for k, v in self.models.items() if k != v.meta.cycle_id]
        if duplicate_ids:
            raise ValueError("dict keys must match model.meta.cycle_id")
        self._meta_index = pd.DataFrame(
            [
                {
                    "cycle_id": model.meta.cycle_id,
                    "latitude": model.meta.latitude,
                    "longitude": model.meta.longitude,
                    "timestamp": model.meta.timestamp,
                    "pressure_min": model.meta.profile_pressure[0],
                    "pressure_max": model.meta.profile_pressure[1],
                }
                for model in self.models.values()
            ]
        ).set_index("cycle_id")

    def __len__(self) -> int:
        return len(self.models)

    def __iter__(self) -> Iterator[Model]:
        return iter(self.models.values())

    def __getitem__(self, cycle_id: str) -> Model:
        return self.models[cycle_id]

    @property
    def index(self) -> pd.DataFrame:
        return self._meta_index.copy()

    def filter(self,
               lat: Optional[tuple[float, float]] = None,
               long: Optional[tuple[float, float]] = None,
               timestamp: Optional[tuple[datetime, datetime]] = None,
               cyclical_dates: Optional[tuple[datetime, datetime]] = None,
               ) -> CycleModels:

        masks = []
        if lat is not None:
            masks.append(self._meta_index.latitude.between(*lat))
        if long is not None:
            masks.append(self._meta_index.longitude.between(*long))
        if timestamp is not None:
            masks.append(self._meta_index.timestamp.between(*timestamp))
        if cyclical_dates is not None:
            ts_norm = self._meta_index['timestamp'].apply(lambda x: x.replace(year=2000))
            filter_norm = tuple(filter_date.replace(year=2000) for filter_date in cyclical_dates)
            if filter_norm[0] <= filter_norm[1]:
                mask = (ts_norm >= filter_norm[0]) & (ts_norm <= filter_norm[1])
            else:
                mask = (ts_norm >= filter_norm[0]) | (ts_norm <= filter_norm[1])
            masks.append(mask)

        index = self.index
        for mask in masks:
            index = index.loc[mask]

        models = {cycle_id: model
                  for cycle_id, model
                  in self.models.items()
                  if cycle_id in index.index}

        return type(self)(models=models)

    def pop(self, cycle_id: str) -> Model:
        model = self.models.pop(cycle_id)
        self._meta_index = self._meta_index.drop(cycle_id)
        return model

    def interpolate(self, pressure_data: ArrayLike) -> CycleData:
        pressure_data = pd.Series(pressure_data, name='pressure')
        temp_data = []
        sal_data = []
        for cycle_id, model in self.models.items():
            model_interp = model.interpolate(pressure_data)
            temp_data.append(pd.Series(model_interp.temperature, index=model_interp.pressure, name=cycle_id))
            sal_data.append(pd.Series(model_interp.salinity, index=model_interp.pressure, name=cycle_id))
        temp_data = pd.concat(temp_data, axis=1)
        sal_data = pd.concat(sal_data, axis=1)
        cycle_data = CycleData(temperature=temp_data, salinity=sal_data)
        return cycle_data

    def interp_error(self, pressure_data: ArrayLike) -> CycleData:
        pressure_data = pd.Series(pressure_data, name='pressure')
        temp_data = []
        sal_data = []
        for cycle_id, model in self.models.items():
            model_interp = model.interp_error(pressure_data)
            temp_data.append(pd.Series(model_interp.temperature, index=model_interp.pressure, name=cycle_id))
            sal_data.append(pd.Series(model_interp.salinity, index=model_interp.pressure, name=cycle_id))
        temp_data = pd.concat(temp_data, axis=1)
        sal_data = pd.concat(sal_data, axis=1)
        cycle_data = CycleData(temperature=temp_data, salinity=sal_data)
        return cycle_data
