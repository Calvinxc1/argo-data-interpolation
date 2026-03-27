from numpy.typing import ArrayLike
from scipy.interpolate import LSQUnivariateSpline

from .build_spline_model import build_spline_model
from .CycleSettings import CycleSettings
from .knot_identifier import knot_identifier
from .uniformed_pressure import uniformed_pressure


def build_model(
    pressure_data: ArrayLike,
    measure_data: ArrayLike,
    settings: CycleSettings,
) -> LSQUnivariateSpline:
    uniform_pressure = uniformed_pressure(pressure_data, settings)
    pressure_knot_temp = knot_identifier(uniform_pressure, pressure_data, measure_data, settings)
    spline_model = build_spline_model(pressure_data, measure_data, pressure_knot_temp, settings)
    return spline_model
