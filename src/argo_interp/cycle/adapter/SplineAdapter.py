import numpy as np
from numpy.typing import NDArray, ArrayLike
from typing import Any, Self
from dataclasses import dataclass
from scipy.interpolate import make_splrep

from .BaseAdapter import BaseAdapter


@dataclass
class SplineAdapter(BaseAdapter):
    model: Any

    @classmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any] = None
            ) -> Self:
        if model_kwargs is None:
            model_kwargs = {}

        model = make_splrep(pressure_data, measure_data, **model_kwargs)
        return cls(model=model)

    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data)

    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        return self.model(pressure_data, nu=1)
