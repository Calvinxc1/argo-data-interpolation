import numpy as np
from abc import ABC, abstractmethod
from numpy.typing import NDArray, ArrayLike
from typing import Any, Self
from dataclasses import dataclass


@dataclass
class BaseAdapter(ABC):
    @classmethod
    @abstractmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any] = None,
            ) -> Self:
        pass

    @abstractmethod
    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        pass

    @abstractmethod
    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        pass
