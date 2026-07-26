from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class MeasureErrorVariance:
    sensor_precision: NDArray[np.float64]
    pressure_gradient: NDArray[np.float64]
    vertical_model: NDArray[np.float64]

    def __post_init__(self) -> None:
        if (
            self.sensor_precision.ndim != 1
            or self.pressure_gradient.ndim != 1
            or self.vertical_model.ndim != 1
        ):
            raise ValueError("MeasureErrorVariance arrays must be one-dimensional")

        if not (
            len(self.sensor_precision)
            == len(self.pressure_gradient)
            == len(self.vertical_model)
        ):
            raise ValueError("MeasureErrorVariance arrays must have the same length")

    @property
    def total(self) -> NDArray[np.float64]:
        return self.sensor_precision + self.pressure_gradient + self.vertical_model

    @property
    def sigma(self) -> NDArray[np.float64]:
        return np.sqrt(self.total)
