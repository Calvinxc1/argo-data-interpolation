import numpy as np

from argo_kwsi.acoustics import (
    SoundSpeedPartials,
    sound_speed_teos10,
    sound_speed_teos10_partials,
    sound_speed_variance,
)


def test_sound_speed_variance_uses_independent_temperature_salinity_terms() -> None:
    partials = SoundSpeedPartials(
        temperature=np.array([2.0, 3.0]),
        salinity=np.array([0.5, 0.25]),
    )

    result = sound_speed_variance(
        temperature_variance=np.array([4.0, 9.0]),
        salinity_variance=np.array([16.0, 25.0]),
        partials=partials,
    )

    expected = np.array(
        [
            2.0**2 * 4.0 + 0.5**2 * 16.0,
            3.0**2 * 9.0 + 0.25**2 * 25.0,
        ]
    )
    np.testing.assert_allclose(result, expected)


def test_sound_speed_helpers_return_finite_teos10_values() -> None:
    pressure = np.array([5.0, 110.0, 500.0])
    temperature = np.array([28.0, 18.0, 8.0])
    salinity = np.array([34.0, 35.0, 35.2])
    longitude = np.full(3, 88.0)
    latitude = np.full(3, 15.0)

    teos10 = sound_speed_teos10(salinity, temperature, pressure, longitude, latitude)
    teos10_partials = sound_speed_teos10_partials(
        salinity,
        temperature,
        pressure,
        longitude,
        latitude,
    )

    assert teos10.shape == pressure.shape
    assert np.isfinite(teos10).all()
    assert np.isfinite(teos10_partials.temperature).all()
    assert np.isfinite(teos10_partials.salinity).all()
