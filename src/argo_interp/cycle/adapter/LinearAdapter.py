import numpy as np
from numpy.typing import NDArray, ArrayLike
from typing import Any, Self
from dataclasses import dataclass
from scipy.interpolate import BSpline, make_interp_spline

from .BaseAdapter import BaseAdapter


@dataclass
class LinearAdapter(BaseAdapter):
    model: BSpline

    @classmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any] = None,
            ) -> Self:
        if model_kwargs is None:
            model_kwargs = {'k': 1}
        else:
            model_kwargs = {**model_kwargs, 'k': 1}

        model = make_interp_spline(pressure_data, measure_data, **model_kwargs)
        return cls(model=model)

    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data)

    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data, nu=1)
