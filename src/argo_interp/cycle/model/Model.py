import numpy as np
from numpy.typing import NDArray, ArrayLike
from typing import Any, Optional, Self
from dataclasses import dataclass, field

from .CycleError import CycleError, MeasureError
from .ModelAdapters import ModelAdapters
from .ModelData import ModelData
from .ModelSettings import ModelSettings
from ..adapter import BaseAdapter
from ..validation import calc_fold_error


@dataclass
class Model:
    adapter: ModelAdapters = field(repr=False)
    error: CycleError
    settings: ModelSettings

    @classmethod
    def build(cls, model_data: ModelData, adapter: BaseAdapter, n_folds: int,
              sensor_accuracy: dict[str, float], model_kwargs: Optional[dict[str, Any]] = None) -> Self:

        temp_error, sal_error = calc_fold_error(model_data, n_folds, adapter, model_kwargs)
        temp_adapter = adapter.fit(model_data.pressure, model_data.temperature, model_kwargs)
        sal_adapter = adapter.fit(model_data.pressure, model_data.salinity, model_kwargs)
        model = cls(
            adapter=ModelAdapters(temperature=temp_adapter, salinity=sal_adapter),
            error=CycleError(
                pressure=sensor_accuracy['pressure'],
                temperature=MeasureError(model=temp_error, sensor=sensor_accuracy['temperature']),
                salinity=MeasureError(model=sal_error, sensor=sensor_accuracy['salinity']),
            ),
            settings=ModelSettings(n_folds, model_kwargs),
        )
        return model

    def interpolate(self, pressure_data: ArrayLike) -> ModelData:
        temp_data = self.adapter.temperature.interpolate(pressure_data)
        sal_data = self.adapter.salinity.interpolate(pressure_data)
        interp_data = ModelData(pressure=pressure_data, temperature=temp_data, salinity=sal_data)
        return interp_data

    def interp_error(self, pressure_data: ArrayLike) -> ModelData:
        temp_error = self._measure_error(self.error.pressure, self.error.temperature,
                                         self.adapter.temperature.gradient(pressure_data))
        sal_error = self._measure_error(self.error.pressure, self.error.salinity,
                                         self.adapter.salinity.gradient(pressure_data))
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
