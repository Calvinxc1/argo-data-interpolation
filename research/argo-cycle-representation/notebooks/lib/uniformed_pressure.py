from numpy import arange
from numpy.typing import ArrayLike, NDArray

from .CycleSettings import CycleSettings


def uniformed_pressure(pressure_data: ArrayLike, settings: CycleSettings) -> NDArray:
    uniform_pressure = arange(pressure_data.min() - settings.spacing,
                              pressure_data.max() + settings.spacing,
                              settings.spacing)
    return uniform_pressure
