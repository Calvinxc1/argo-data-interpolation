from dataclasses import dataclass

import gsw
import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True, slots=True)
class SoundSpeedPartials:
    temperature: NDArray[np.float64]
    salinity: NDArray[np.float64]


def sound_speed_teos10(
    practical_salinity: ArrayLike,
    temperature: ArrayLike,
    pressure: ArrayLike,
    longitude: ArrayLike,
    latitude: ArrayLike,
) -> NDArray[np.float64]:
    absolute_salinity = gsw.SA_from_SP(practical_salinity, pressure, longitude, latitude)
    conservative_temperature = gsw.CT_from_t(absolute_salinity, temperature, pressure)
    return np.asarray(
        gsw.sound_speed(absolute_salinity, conservative_temperature, pressure),
        dtype=float,
    )


def sound_speed_teos10_partials(
    practical_salinity: ArrayLike,
    temperature: ArrayLike,
    pressure: ArrayLike,
    longitude: ArrayLike,
    latitude: ArrayLike,
    *,
    temperature_step: float = 1e-3,
    salinity_step: float = 1e-3,
) -> SoundSpeedPartials:
    practical_salinity = np.asarray(practical_salinity, dtype=float)
    temperature = np.asarray(temperature, dtype=float)
    pressure = np.asarray(pressure, dtype=float)

    dc_dtemperature = (
        sound_speed_teos10(
            practical_salinity,
            temperature + temperature_step,
            pressure,
            longitude,
            latitude,
        )
        - sound_speed_teos10(
            practical_salinity,
            temperature - temperature_step,
            pressure,
            longitude,
            latitude,
        )
    ) / (2 * temperature_step)
    dc_dsalinity = (
        sound_speed_teos10(
            practical_salinity + salinity_step,
            temperature,
            pressure,
            longitude,
            latitude,
        )
        - sound_speed_teos10(
            practical_salinity - salinity_step,
            temperature,
            pressure,
            longitude,
            latitude,
        )
    ) / (2 * salinity_step)

    return SoundSpeedPartials(temperature=dc_dtemperature, salinity=dc_dsalinity)


def sound_speed_variance(
    temperature_variance: ArrayLike,
    salinity_variance: ArrayLike,
    partials: SoundSpeedPartials,
) -> NDArray[np.float64]:
    temperature_variance = np.asarray(temperature_variance, dtype=float)
    salinity_variance = np.asarray(salinity_variance, dtype=float)
    return partials.temperature**2 * temperature_variance + partials.salinity**2 * salinity_variance
