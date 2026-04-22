from dataclasses import dataclass
from typing import Any, Self

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.interpolate import PchipInterpolator

from .BaseAdapter import BaseAdapter


@dataclass
class PchipAdapter(BaseAdapter):
    model: PchipInterpolator

    @classmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any]) -> Self:
        model_kwargs = {'extrapolate': False, **model_kwargs}
        model = PchipInterpolator(x=pressure_data, y=measure_data, **model_kwargs)
        return cls(model=model)

    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data)

    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data, nu=1)
