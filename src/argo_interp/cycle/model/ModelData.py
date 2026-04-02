from dataclasses import dataclass
from numpy.typing import NDArray
import numpy as np


@dataclass(frozen=True, slots=True)
class ModelData:
    pressure: NDArray[np.float64]
    temperature: NDArray[np.float64]
    salinity: NDArray[np.float64]
