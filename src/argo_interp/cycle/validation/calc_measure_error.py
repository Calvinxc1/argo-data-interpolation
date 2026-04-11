import numpy as np
from numpy.typing import NDArray

from ..adapter.BaseAdapter import BaseAdapter


def calc_measure_error(adapter: BaseAdapter, pressure_data: NDArray[np.float64],
                      measure_data: NDArray[np.float64]) -> float:
    predict = adapter.interpolate(pressure_data)
    error = measure_data - predict
    square_sum_error = (error ** 2).sum()
    return square_sum_error
