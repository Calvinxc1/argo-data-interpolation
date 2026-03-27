from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from scipy.interpolate import BSpline, LSQUnivariateSpline

from .CycleError import CycleError
from .CycleError import ModelError, SensorError
from .CycleSettings import CycleSettings


@dataclass(frozen=True, slots=True)
class CycleModel:
    temperature: LSQUnivariateSpline
    salinity: LSQUnivariateSpline
    error: CycleError
    settings: CycleSettings
    pressure_bounds: tuple[float, float] = (0, 2_000)

    _STATE_VERSION = 1

    def interpolate(self, pressure_values: ArrayLike) -> pd.DataFrame:
        pressure_values = np.asarray(pressure_values, dtype=float)
        self._validate_domain(pressure_values)

        interpolation = self._calc_interp(pressure_values)
        errors = self._calc_errors(pressure_values)

        interp_final = pd.concat([interpolation, errors], axis=1)
        return interp_final

    def _calc_interp(self, pressure_values: ArrayLike) -> pd.DataFrame:
        array_interpolation = np.stack(
            [
                self.temperature(pressure_values),
                self.salinity(pressure_values),
            ],
            axis=-1,
        )
        frame_index = pd.Series(pressure_values, name="pressure")
        dataframe_interpolation = pd.DataFrame(
            array_interpolation,
            index=frame_index,
            columns=["temperature", "salinity"],
        )
        return dataframe_interpolation

    def _calc_errors(self, pressure_values: ArrayLike) -> pd.DataFrame:
        array_interpolation = np.stack(
            [
                self.temperature(pressure_values, nu=1),
                self.salinity(pressure_values, nu=1),
            ],
            axis=-1,
        )
        array_errors = np.abs(array_interpolation) * self.error.sensor.pressure
        frame_index = pd.Series(pressure_values, name="pressure")
        frame_errors = pd.DataFrame(
            array_errors,
            index=frame_index,
            columns=["temp_error", "sal_error"],
        )

        frame_errors = frame_errors ** 2
        frame_errors["temp_error"] += (
            self.error.sensor.temperature ** 2
        ) + (self.error.model.temperature ** 2)
        frame_errors["sal_error"] += (
            self.error.sensor.salinity ** 2
        ) + (self.error.model.salinity ** 2)
        frame_errors = np.sqrt(frame_errors)
        return frame_errors

    def _validate_domain(self, pressure_values: NDArray[np.float64]) -> None:
        pressure_min, pressure_max = self.pressure_bounds
        if np.any(pressure_values < pressure_min) or np.any(pressure_values > pressure_max):
            raise ValueError(
                f"`pressure_values` must be within [{pressure_min:.3f}, {pressure_max:.3f}]"
            )

    def to_state(self) -> tuple:
        # Keep pickle state compact and versioned without changing the live object layout.
        return (
            self._STATE_VERSION,
            self.temperature.t,
            self.temperature.c,
            self.temperature.k,
            self.salinity.t,
            self.salinity.c,
            self.salinity.k,
            self.error.model.temperature,
            self.error.model.salinity,
            self.error.sensor.pressure,
            self.error.sensor.temperature,
            self.error.sensor.salinity,
            self.settings.prominence,
            self.settings.window,
            self.settings.spacing,
            self.settings.peak_dist,
            self.settings.folds,
            self.pressure_bounds,
        )

    @classmethod
    def from_state(cls, state: tuple) -> "CycleModel":
        (
            version,
            temp_t,
            temp_c,
            temp_k,
            sal_t,
            sal_c,
            sal_k,
            model_temp_error,
            model_sal_error,
            sensor_pressure_error,
            sensor_temp_error,
            sensor_sal_error,
            prominence,
            window,
            spacing,
            peak_dist,
            folds,
            pressure_bounds,
        ) = state

        if version != cls._STATE_VERSION:
            raise ValueError(f"Unsupported CycleModel state version: {version}")

        return cls(
            temperature=BSpline(temp_t, temp_c, temp_k),
            salinity=BSpline(sal_t, sal_c, sal_k),
            error=CycleError(
                model=ModelError(
                    temperature=model_temp_error,
                    salinity=model_sal_error,
                ),
                sensor=SensorError(
                    pressure=sensor_pressure_error,
                    temperature=sensor_temp_error,
                    salinity=sensor_sal_error,
                ),
            ),
            settings=CycleSettings(
                prominence=prominence,
                window=window,
                spacing=spacing,
                peak_dist=peak_dist,
                folds=folds,
            ),
            pressure_bounds=pressure_bounds,
        )

    def __reduce__(self) -> tuple:
        # Pickle through the compact tuple state rather than the full Python object graph.
        return (self.__class__.from_state, (self.to_state(),))
