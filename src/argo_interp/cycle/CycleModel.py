from dataclasses import dataclass
import numpy as np
from numpy.typing import ArrayLike, NDArray
import pandas as pd
from scipy.interpolate import LSQUnivariateSpline

from .CycleError import CycleError
from .CycleSettings import CycleSettings


@dataclass
class CycleModel:
    temperature: LSQUnivariateSpline
    salinity: LSQUnivariateSpline
    error: CycleError
    settings: CycleSettings
    pressure_bounds: tuple[float, float] = (0, 2_000)

    def interpolate(self, pressure_values: ArrayLike) -> pd.DataFrame:
        pressure_values = np.asarray(pressure_values, dtype=float)
        self._validate_domain(pressure_values)

        interpolation = self._calc_interp(pressure_values)
        errors = self._calc_errors(pressure_values)

        interp_final = pd.concat([interpolation, errors], axis=1)
        return interp_final

    def _calc_interp(self, pressure_values: ArrayLike) -> pd.DataFrame:
        array_interpolation = np.stack([
            self.temperature(pressure_values),
            self.salinity(pressure_values)
        ], axis=-1)
        frame_index = pd.Series(pressure_values, name='pressure')
        dataframe_interpolation = pd.DataFrame(array_interpolation, index=frame_index, columns=['temperature', 'salinity'])
        return dataframe_interpolation

    def _calc_errors(self, pressure_values: ArrayLike) -> pd.DataFrame:
        array_interpolation = np.stack([
            self.temperature(pressure_values, nu=1),
            self.salinity(pressure_values, nu=1)
        ], axis=-1)
        array_errors = np.abs(array_interpolation) * self.error.sensor.pressure
        frame_index = pd.Series(pressure_values, name='pressure')
        frame_errors = pd.DataFrame(array_errors, index=frame_index, columns=['temp_error', 'sal_error'])

        frame_errors = frame_errors ** 2
        frame_errors['temp_error'] += (self.error.sensor.temperature ** 2) + (self.error.model.temperature ** 2)
        frame_errors['sal_error'] += (self.error.sensor.salinity ** 2) + (self.error.model.salinity ** 2)
        frame_errors = np.sqrt(frame_errors)
        return frame_errors

    def _validate_domain(self, pressure_values: NDArray[np.float64]) -> None:
        pressure_min, pressure_max = self.pressure_bounds
        if np.any(pressure_values < pressure_min) or np.any(pressure_values > pressure_max):
            raise ValueError(
                f"`pressure_values` must be within [{pressure_min:.3f}, {pressure_max:.3f}]"
            )
