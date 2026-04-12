import numpy as np
from numpy.typing import NDArray, ArrayLike
from typing import Self
from dataclasses import dataclass, field

from .ModelAdapters import ModelAdapters
from ..adapter.BaseAdapter import BaseAdapter
from ..config.ModelSettings import ModelSettings
from ..domain.CycleError import CycleError
from ..domain.MeasureError import MeasureError
from ..domain.ModelData import ModelData
from ..domain.ModelMeta import ModelMeta
from ..validation.calc_fold_error import calc_fold_error


@dataclass
class Model:
    meta: ModelMeta
    adapters: ModelAdapters = field(repr=False)
    error: CycleError
    settings: ModelSettings

    @classmethod
    def build(cls, model_meta: ModelMeta, model_data: ModelData, adapter: BaseAdapter, settings: ModelSettings) -> Self:
        temp_error, sal_error = calc_fold_error(model_data, adapter, settings)

        temp_adapter = adapter.fit(model_data.pressure, model_data.temperature, settings.model_kwargs.temperature)
        sal_adapter = adapter.fit(model_data.pressure, model_data.salinity, settings.model_kwargs.salinity)

        adapters = ModelAdapters(temperature=temp_adapter, salinity=sal_adapter)
        error = CycleError(
            pressure=settings.sensor_accuracy.pressure,
            temperature=MeasureError(model=temp_error, sensor=settings.sensor_accuracy.temperature),
            salinity=MeasureError(model=sal_error, sensor=settings.sensor_accuracy.salinity),
        )

        model = cls(meta=model_meta, adapters=adapters, error=error, settings=settings)
        return model

    def interpolate(self, pressure_data: ArrayLike | float) -> ModelData:
        if isinstance(pressure_data, float):
            pressure_data = np.array([pressure_data])
        else:
            pressure_data = np.asarray(pressure_data, dtype=float)

        temp_data = self.adapters.temperature.interpolate(pressure_data)
        sal_data = self.adapters.salinity.interpolate(pressure_data)
        interp_data = ModelData(pressure=pressure_data, temperature=temp_data, salinity=sal_data)
        return interp_data

    def interp_error(self, pressure_data: ArrayLike | float) -> ModelData:
        if isinstance(pressure_data, float):
            pressure_data = np.array([pressure_data])
        else:
            pressure_data = np.asarray(pressure_data, dtype=float)

        temp_error = self._measure_error(self.error.pressure, self.error.temperature,
                                         self.adapters.temperature.gradient(pressure_data))
        sal_error = self._measure_error(self.error.pressure, self.error.salinity,
                                         self.adapters.salinity.gradient(pressure_data))
        interp_error = ModelData(pressure=pressure_data, temperature=temp_error, salinity=sal_error)
        return interp_error

    @staticmethod
    def _measure_error(pressure_error: float, measure_error: MeasureError,
                       measure_gradient: NDArray[np.float64]) -> NDArray[np.float64]:
        sq_model_error = measure_error.model ** 2
        sq_sensor_error = measure_error.sensor ** 2
        sq_pres_error = (np.abs(measure_gradient) * pressure_error) ** 2

        measure_errors = np.sqrt(sq_model_error + sq_sensor_error + sq_pres_error)
        return measure_errors
