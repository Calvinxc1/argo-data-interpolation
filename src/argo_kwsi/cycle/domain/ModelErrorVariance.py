from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .MeasureErrorVariance import MeasureErrorVariance
from .ModelData import ModelData


@dataclass(frozen=True, slots=True)
class ModelErrorVariance:
    pressure: NDArray[np.float64]
    temperature: MeasureErrorVariance
    salinity: MeasureErrorVariance

    def __post_init__(self) -> None:
        if self.pressure.ndim != 1:
            raise ValueError("pressure must be one-dimensional")

        if len(self.temperature.total) != len(self.pressure) or len(self.salinity.total) != len(
            self.pressure
        ):
            raise ValueError("variance component lengths must match pressure length")

    @property
    def total(self) -> ModelData:
        return ModelData(
            pressure=self.pressure,
            temperature=self.temperature.total,
            salinity=self.salinity.total,
        )

    @property
    def sigma(self) -> ModelData:
        return ModelData(
            pressure=self.pressure,
            temperature=self.temperature.sigma,
            salinity=self.salinity.sigma,
        )
