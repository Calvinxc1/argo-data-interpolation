from numpy import abs, interp
from numpy.typing import ArrayLike
from scipy.signal import find_peaks, savgol_filter

from .calc_polyorder import calc_polyorder
from .CycleSettings import CycleSettings


def knot_identifier(
    uniform_pressure: ArrayLike,
    pressure_data: ArrayLike,
    readings_data: ArrayLike,
    settings: CycleSettings,
) -> ArrayLike:
    polyorder = calc_polyorder(settings.window)
    uniform_readings = interp(uniform_pressure, pressure_data, readings_data)
    smooth_uniform_readings = savgol_filter(
        uniform_readings,
        window_length=settings.window,
        polyorder=polyorder,
    )

    curvature_uniform_readings = abs(
        savgol_filter(
            smooth_uniform_readings,
            window_length=settings.window,
            polyorder=polyorder,
            deriv=2,
            delta=settings.spacing,
        )
    )
    peak_idx, _ = find_peaks(
        curvature_uniform_readings,
        prominence=settings.prominence * curvature_uniform_readings.std(),
        distance=settings.peak_dist,
    )
    pressure_knot_values = uniform_pressure[peak_idx]

    return pressure_knot_values
