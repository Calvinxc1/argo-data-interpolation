import numpy as np

from argo_interp.cycle.calc_rmse import calc_rmse


def test_calc_rmse_is_zero_for_exact_match() -> None:
    actual = np.array([1.0, 2.0, 3.0])
    predicted = np.array([1.0, 2.0, 3.0])

    assert calc_rmse(actual, predicted) == 0.0


def test_calc_rmse_matches_known_value() -> None:
    actual = np.array([1.0, 3.0])
    predicted = np.array([0.0, 1.0])

    expected = np.sqrt(((1.0 - 0.0) ** 2 + (3.0 - 1.0) ** 2) / 2.0)
    assert np.isclose(calc_rmse(actual, predicted), expected)
