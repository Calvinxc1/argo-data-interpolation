import numpy as np
from scipy.interpolate import PchipInterpolator
from numpy.typing import NDArray, ArrayLike
from typing import Any, Self
from dataclasses import dataclass

from .BaseAdapter import BaseAdapter


@dataclass
class PchipAdapter(BaseAdapter):
    model: PchipInterpolator

    @classmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any] = None,
            ) -> Self:
        if model_kwargs is None:
            model_kwargs = {'extrapolate': False}
        else:
            model_kwargs = {'extrapolate': False, **model_kwargs}

        model = PchipInterpolator(x=pressure_data, y=measure_data, **model_kwargs)
        return cls(model=model)

    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data)

    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data, nu=1)
