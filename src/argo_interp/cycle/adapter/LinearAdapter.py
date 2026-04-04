import numpy as np
from numpy.typing import NDArray, ArrayLike
from typing import Any, Self
from dataclasses import dataclass
from scipy.interpolate import BSpline

from .BaseAdapter import BaseAdapter


@dataclass
class LinearAdapter(BaseAdapter):
    model: BSpline

    @classmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any]) -> Self:
        model_kwargs = {'extrapolate': False, **model_kwargs, 'k': 1}
        knots = np.concatenate([[pressure_data[0]], pressure_data, [pressure_data[-1]]])
        model = BSpline(knots, measure_data, **model_kwargs)
        return cls(model=model)

    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data)

    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data, nu=1)
