import warnings
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

SoundSpeedFormulation = Literal["EOS-80", "TEOS-10"]


def calc_sound_speed(
    temperature: ArrayLike,
    salinity: ArrayLike,
    pressure: ArrayLike,
    formulation: SoundSpeedFormulation = "EOS-80",
) -> NDArray[np.float64]:
    formulation = _normalize_formulation(formulation)

    if formulation == "EOS-80":
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, message=".*seawater.*")
            import seawater as sw

        return sw.svel(salinity, temperature, pressure)

    import gsw

    return gsw.sound_speed(salinity, temperature, pressure)


def propagate_sound_speed_uncertainty(
    temperature: ArrayLike,
    salinity: ArrayLike,
    pressure: ArrayLike,
    sigma_temperature: ArrayLike,
    sigma_salinity: ArrayLike,
    sigma_pressure: ArrayLike,
    formulation: SoundSpeedFormulation = "EOS-80",
    h_temperature: float = 1e-3,
    h_salinity: float = 1e-3,
    h_pressure: float = 1e-2,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    First-order Taylor propagation of input uncertainty to sound speed.
    Assumes independent input errors. Returns (sound_speed, sigma_sound_speed).

    Limitations:
    - Linearization degrades as input uncertainty grows, especially when
      temperature uncertainty exceeds roughly 1 degree C.
    - Cross-covariance terms are omitted; this is incomplete for
      spatiotemporal products with correlated temperature and salinity errors.
    - Finite-difference steps are conservative defaults, not adaptive steps for
      extreme cold or deep regimes.
    """
    (
        temperature,
        salinity,
        pressure,
        sigma_temperature,
        sigma_salinity,
        sigma_pressure,
    ) = np.broadcast_arrays(
        np.asarray(temperature, dtype=float),
        np.asarray(salinity, dtype=float),
        np.asarray(pressure, dtype=float),
        np.asarray(sigma_temperature, dtype=float),
        np.asarray(sigma_salinity, dtype=float),
        np.asarray(sigma_pressure, dtype=float),
    )

    sound_speed = calc_sound_speed(temperature, salinity, pressure, formulation)
    dcdt = _central_difference(
        temperature,
        salinity,
        pressure,
        formulation,
        variable="temperature",
        step=h_temperature,
    )
    dcds = _central_difference(
        temperature,
        salinity,
        pressure,
        formulation,
        variable="salinity",
        step=h_salinity,
    )
    dcdp = _central_difference(
        temperature,
        salinity,
        pressure,
        formulation,
        variable="pressure",
        step=h_pressure,
    )

    variance = (
        np.square(dcdt * sigma_temperature)
        + np.square(dcds * sigma_salinity)
        + np.square(dcdp * sigma_pressure)
    )
    return sound_speed, np.sqrt(variance)


def _central_difference(
    temperature: NDArray[np.float64],
    salinity: NDArray[np.float64],
    pressure: NDArray[np.float64],
    formulation: SoundSpeedFormulation,
    *,
    variable: Literal["temperature", "salinity", "pressure"],
    step: float,
) -> NDArray[np.float64]:
    if not np.isfinite(step) or step <= 0:
        raise ValueError("finite difference steps must be finite positive floats")

    temp_plus = temperature
    temp_minus = temperature
    sal_plus = salinity
    sal_minus = salinity
    pres_plus = pressure
    pres_minus = pressure

    if variable == "temperature":
        temp_plus = temperature + step
        temp_minus = temperature - step
    elif variable == "salinity":
        sal_plus = salinity + step
        sal_minus = salinity - step
    else:
        pres_plus = pressure + step
        pres_minus = pressure - step

    plus = calc_sound_speed(temp_plus, sal_plus, pres_plus, formulation)
    minus = calc_sound_speed(temp_minus, sal_minus, pres_minus, formulation)
    return (plus - minus) / (2.0 * step)


def _normalize_formulation(formulation: str) -> SoundSpeedFormulation:
    normalized = formulation.upper()
    if normalized in {"EOS-80", "EOS80", "CHEN-MILLERO", "CHEN_MILLERO"}:
        return "EOS-80"
    if normalized in {"TEOS-10", "TEOS10", "GSW"}:
        return "TEOS-10"
    raise ValueError("formulation must be 'EOS-80' or 'TEOS-10'")
