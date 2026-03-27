from numpy.typing import ArrayLike
from scipy.interpolate import make_lsq_spline

from .calc_polyorder import calc_polyorder
from .CycleSettings import CycleSettings


def build_spline_model(
    uniform_pressure: ArrayLike,
    smooth_uniform_readings: ArrayLike,
    pressure_knot_vals: ArrayLike,
    settings: CycleSettings,
):
    def build_t(
        uniform_pressure: ArrayLike,
        pressure_knot_vals: ArrayLike,
        polyorder: int,
    ) -> list[float]:

        t = [
            *[uniform_pressure.min()] * (polyorder + 1),
            *pressure_knot_vals,
            *[uniform_pressure.max()] * (polyorder + 1),
        ]
        return t

    polyorder = calc_polyorder(settings.window)
    t = build_t(uniform_pressure, pressure_knot_vals, polyorder)
    spline_model = make_lsq_spline(uniform_pressure, smooth_uniform_readings, t=t, k=polyorder)
    return spline_model
