import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from argo_kwsi.model.CycleData import CycleData

PREDICTION_PATH = (
    Path(__file__).parents[1]
    / "research"
    / "underwater-acoustics"
    / "notebooks"
    / "lib"
    / "prediction.py"
)
SPEC = importlib.util.spec_from_file_location("underwater_acoustics_prediction", PREDICTION_PATH)
prediction = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(prediction)


def test_weighted_profile_variance_uses_squared_normalized_weights() -> None:
    variances = np.array(
        [
            [4.0, 9.0],
            [np.nan, 16.0],
            [np.nan, np.nan],
        ]
    )
    weights = np.array([1.0, 3.0])

    result = prediction.weighted_profile_variance(variances, weights)

    expected_first = (1.0 / 4.0) ** 2 * 4.0 + (3.0 / 4.0) ** 2 * 9.0
    expected_second = 1.0**2 * 16.0
    np.testing.assert_allclose(result[:2], np.array([expected_first, expected_second]))
    assert np.isnan(result[2])


def test_weighted_profile_mean_returns_nan_without_finite_support() -> None:
    values = np.array(
        [
            [2.0, 4.0],
            [np.nan, np.nan],
        ]
    )
    weights = np.array([1.0, 3.0])

    result = prediction.weighted_profile_mean(values, weights)

    np.testing.assert_allclose(result[0], 3.5)
    assert np.isnan(result[1])


def test_weighted_cycle_variance_applies_helper_to_temperature_and_salinity() -> None:
    pressure = pd.Index([10.0, 20.0], name="pressure")
    interp_variance = CycleData(
        temperature=pd.DataFrame({"a": [4.0, np.nan], "b": [9.0, 16.0]}, index=pressure),
        salinity=pd.DataFrame({"a": [1.0, 4.0], "b": [9.0, 16.0]}, index=pressure),
    )
    weights = np.array([1.0, 3.0])

    temp_variance, sal_variance = prediction.weighted_cycle_variance(interp_variance, weights)

    np.testing.assert_allclose(temp_variance, np.array([5.3125, 16.0]))
    np.testing.assert_allclose(sal_variance, np.array([5.125, 9.25]))
