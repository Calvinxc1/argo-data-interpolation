import numpy as np

from argo_interp.cycle.sound_speed import calc_sound_speed, propagate_sound_speed_uncertainty


def test_calc_sound_speed_dispatches_eos80_and_teos10() -> None:
    pressure = np.array([100.0])
    temperature = np.array([10.0])
    salinity = np.array([35.0])

    eos80 = calc_sound_speed(temperature, salinity, pressure, formulation="EOS-80")
    teos10 = calc_sound_speed(temperature, salinity, pressure, formulation="TEOS-10")

    np.testing.assert_allclose(eos80, np.array([1491.47747657]))
    np.testing.assert_allclose(teos10, np.array([1491.30944014]))


def test_propagate_sound_speed_uncertainty_matches_reference_derivative_scale() -> None:
    sound_speed, sigma = propagate_sound_speed_uncertainty(
        temperature=np.array([10.0]),
        salinity=np.array([35.0]),
        pressure=np.array([100.0]),
        sigma_temperature=np.array([0.002]),
        sigma_salinity=np.array([0.01]),
        sigma_pressure=np.array([2.4]),
    )

    dcdt = (calc_sound_speed([10.001], [35.0], [100.0])[0] - calc_sound_speed(
        [9.999], [35.0], [100.0]
    )[0]) / 0.002
    dcds = (calc_sound_speed([10.0], [35.001], [100.0])[0] - calc_sound_speed(
        [10.0], [34.999], [100.0]
    )[0]) / 0.002
    dcdp = (calc_sound_speed([10.0], [35.0], [100.01])[0] - calc_sound_speed(
        [10.0], [35.0], [99.99]
    )[0]) / 0.02

    assert sound_speed.shape == (1,)
    assert 3.0 < dcdt < 4.0
    assert 1.0 < dcds < 1.5
    assert 0.015 < dcdp < 0.02
    np.testing.assert_allclose(
        sigma,
        np.sqrt((dcdt * 0.002) ** 2 + (dcds * 0.01) ** 2 + (dcdp * 2.4) ** 2),
    )


def test_propagate_sound_speed_uncertainty_vectorizes() -> None:
    _, sigma = propagate_sound_speed_uncertainty(
        temperature=np.array([10.0, 10.0]),
        salinity=np.array([35.0, 35.0]),
        pressure=np.array([100.0, 100.0]),
        sigma_temperature=np.array([0.002, 0.76]),
        sigma_salinity=0.01,
        sigma_pressure=2.4,
    )

    assert sigma.shape == (2,)
    assert 0.03 < sigma[0] < 0.05
    assert 2.5 < sigma[1] < 2.8


def test_propagate_sound_speed_uncertainty_accepts_formulation_aliases() -> None:
    canonical, _ = propagate_sound_speed_uncertainty(10.0, 35.0, 100.0, 0.002, 0.01, 2.4)
    alias, _ = propagate_sound_speed_uncertainty(
        10.0,
        35.0,
        100.0,
        0.002,
        0.01,
        2.4,
        formulation="chen-millero",
    )

    np.testing.assert_allclose(alias, canonical)
