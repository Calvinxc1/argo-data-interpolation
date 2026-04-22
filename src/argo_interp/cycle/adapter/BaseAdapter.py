from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Self

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass
class BaseAdapter(ABC):
    @classmethod
    @abstractmethod
    def fit(cls, pressure_data: NDArray[np.float64],
            measure_data: NDArray[np.float64],
            model_kwargs: dict[str, Any]) -> Self:
        pass

    @abstractmethod
    def interpolate(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        pass

    @abstractmethod
    def gradient(self, pressure_data: ArrayLike) -> NDArray[np.float64]:
        pass
