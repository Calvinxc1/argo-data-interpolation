from dataclasses import dataclass, field
from typing import Self

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ..adapter.BaseAdapter import BaseAdapter
from ..config.ModelSettings import ModelSettings
from ..domain.CycleError import CycleError
from ..domain.MeasureError import MeasureError
from ..domain.MeasureErrorVariance import MeasureErrorVariance
from ..domain.ModelData import ModelData
from ..domain.ModelErrorVariance import ModelErrorVariance
from ..domain.ModelMeta import ModelMeta
from ..validation.calc_fold_error import calc_fold_error
from .ModelAdapters import ModelAdapters


@dataclass
class Model:
    meta: ModelMeta
    adapters: ModelAdapters = field(repr=False)
    error: CycleError
    settings: ModelSettings

    @classmethod
    def build(
        cls,
        model_meta: ModelMeta,
        model_data: ModelData,
        adapter: BaseAdapter,
        settings: ModelSettings,
    ) -> Self:
        temp_error, sal_error = calc_fold_error(model_data, adapter, settings)

        temp_adapter = adapter.fit(
            model_data.pressure,
            model_data.temperature,
            settings.model_kwargs.temperature,
        )
        sal_adapter = adapter.fit(
            model_data.pressure,
            model_data.salinity,
            settings.model_kwargs.salinity,
        )

        adapters = ModelAdapters(temperature=temp_adapter, salinity=sal_adapter)
        error = CycleError(
            pressure=settings.sensor_accuracy.pressure,
            temperature=MeasureError(model=temp_error, sensor=settings.sensor_accuracy.temperature),
            salinity=MeasureError(model=sal_error, sensor=settings.sensor_accuracy.salinity),
        )

        model = cls(meta=model_meta, adapters=adapters, error=error, settings=settings)
        return model

    @staticmethod
    def _normalize_pressure_input(pressure_data: ArrayLike | float) -> NDArray[np.float64]:
        pressure_array = np.asarray(pressure_data, dtype=float)
        if pressure_array.ndim == 0:
            return pressure_array.reshape(1)
        return pressure_array

    def interpolate(self, pressure_data: ArrayLike | float) -> ModelData:
        pressure_data = self._normalize_pressure_input(pressure_data)

        temp_data = self.adapters.temperature.interpolate(pressure_data)
        sal_data = self.adapters.salinity.interpolate(pressure_data)
        interp_data = ModelData(pressure=pressure_data, temperature=temp_data, salinity=sal_data)
        return interp_data

    def interp_error(self, pressure_data: ArrayLike | float) -> ModelData:
        pressure_data = self._normalize_pressure_input(pressure_data)

        temp_error = self._measure_error(
            self.error.pressure,
            self.error.temperature,
            self.adapters.temperature.gradient(pressure_data),
        )
        sal_error = self._measure_error(
            self.error.pressure,
            self.error.salinity,
            self.adapters.salinity.gradient(pressure_data),
        )
        interp_error = ModelData(pressure=pressure_data, temperature=temp_error, salinity=sal_error)
        return interp_error

    def interp_error_variance(self, pressure_data: ArrayLike | float) -> ModelErrorVariance:
        pressure_data = self._normalize_pressure_input(pressure_data)

        temp_variance = self._measure_error_variance(
            self.error.pressure,
            self.error.temperature,
            self.adapters.temperature.gradient(pressure_data),
        )
        sal_variance = self._measure_error_variance(
            self.error.pressure,
            self.error.salinity,
            self.adapters.salinity.gradient(pressure_data),
        )
        return ModelErrorVariance(
            pressure=pressure_data,
            temperature=temp_variance,
            salinity=sal_variance,
        )

    @staticmethod
    def _measure_error(
        pressure_error: float,
        measure_error: MeasureError,
        measure_gradient: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        return Model._measure_error_variance(
            pressure_error,
            measure_error,
            measure_gradient,
        ).sigma

    @staticmethod
    def _measure_error_variance(
        pressure_error: float,
        measure_error: MeasureError,
        measure_gradient: NDArray[np.float64],
    ) -> MeasureErrorVariance:
        sensor_precision = np.full_like(
            measure_gradient,
            measure_error.sensor**2,
            dtype=float,
        )
        pressure_gradient = (measure_gradient * pressure_error) ** 2
        vertical_model = np.full_like(
            measure_gradient,
            measure_error.model**2,
            dtype=float,
        )

        return MeasureErrorVariance(
            sensor_precision=sensor_precision,
            pressure_gradient=pressure_gradient,
            vertical_model=vertical_model,
        )
