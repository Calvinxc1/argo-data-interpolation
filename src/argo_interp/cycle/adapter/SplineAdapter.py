import numpy as np
from numpy.typing import NDArray, ArrayLike
from typing import Any, Self
from dataclasses import dataclass
from scipy.interpolate import BSpline, make_splrep

from .BaseAdapter import BaseAdapter


@dataclass
class SplineAdapter(BaseAdapter):
    model: BSpline

    @classmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any]) -> Self:
        fit_kwargs = dict(model_kwargs)
        extrapolate = fit_kwargs.pop("extrapolate", False)
        model = make_splrep(pressure_data, measure_data, **fit_kwargs)
        model.extrapolate = extrapolate
        return cls(model=model)

    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data)

    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data, nu=1)
