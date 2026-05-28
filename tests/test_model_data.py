import numpy as np
import pandas as pd
import pytest

from argo_interp.cycle.domain.ModelData import ModelData


def test_model_data_rejects_non_1d_arrays() -> None:
    with pytest.raises(ValueError, match="one-dimensional"):
        ModelData(
            pressure=np.array([[1.0, 2.0]]),
            temperature=np.array([10.0, 11.0]),
            salinity=np.array([35.0, 35.1]),
        )


def test_model_data_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        ModelData(
            pressure=np.array([1.0, 2.0]),
            temperature=np.array([10.0]),
            salinity=np.array([35.0, 35.1]),
        )


def test_model_data_n_obs_and_frame_round_trip() -> None:
    model_data = ModelData(
        pressure=np.array([1.0, 2.0, 3.0]),
        temperature=np.array([10.0, 11.0, 12.0]),
        salinity=np.array([35.0, 35.1, 35.2]),
    )

    assert model_data.n_obs == 3

    frame = model_data.to_frame()
    assert list(frame.columns) == ["pressure", "temperature", "salinity"]

    restored = ModelData.from_frame(frame)
    np.testing.assert_array_equal(restored.pressure, model_data.pressure)
    np.testing.assert_array_equal(restored.temperature, model_data.temperature)
    np.testing.assert_array_equal(restored.salinity, model_data.salinity)


def test_model_data_calculates_sound_speed_from_salinity_temperature_and_pressure() -> None:
    model_data = ModelData(
        pressure=np.array([0.0, 500.0, 1000.0]),
        temperature=np.array([15.0, 10.0, 5.0]),
        salinity=np.array([35.0, 35.0, 35.0]),
    )

    sound_speed = model_data.sound_speed()

    np.testing.assert_allclose(
        sound_speed,
        np.array([1506.67462936, 1498.07495363, 1487.20039663]),
    )


def test_model_data_propagates_sound_speed_uncertainty() -> None:
    model_data = ModelData(
        pressure=np.array([100.0, 200.0]),
        temperature=np.array([10.0, 9.0]),
        salinity=np.array([35.0, 35.1]),
    )

    sound_speed, sigma = model_data.sound_speed_uncertainty(
        sigma_temperature=np.array([0.002, 0.5]),
        sigma_salinity=0.01,
        sigma_pressure=2.4,
    )

    np.testing.assert_allclose(sound_speed, model_data.sound_speed())
    assert sigma.shape == (2,)
    assert sigma[1] > sigma[0]


def test_model_data_from_frame_rejects_missing_columns() -> None:
    frame = pd.DataFrame({"pressure": [1.0], "temperature": [10.0]})

    with pytest.raises(ValueError, match="Missing required columns"):
        ModelData.from_frame(frame)


def test_clean_duplicates_drop_exact_raises_when_pressure_still_not_strictly_increasing() -> None:
    model_data = ModelData(
        pressure=np.array([2.0, 1.0, 1.0, 1.0]),
        temperature=np.array([20.0, 10.0, 10.0, 10.5]),
        salinity=np.array([35.2, 35.0, 35.0, 35.1]),
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        model_data.clean_duplicates(rule="drop_exact")


def test_clean_duplicates_first_keeps_first_pressure_match_after_stable_sort() -> None:
    model_data = ModelData(
        pressure=np.array([2.0, 1.0, 1.0]),
        temperature=np.array([20.0, 10.0, 11.0]),
        salinity=np.array([35.2, 35.0, 35.1]),
    )

    cleaned = model_data.clean_duplicates(rule="first")

    np.testing.assert_array_equal(cleaned.pressure, np.array([1.0, 2.0]))
    np.testing.assert_array_equal(cleaned.temperature, np.array([10.0, 20.0]))
    np.testing.assert_array_equal(cleaned.salinity, np.array([35.0, 35.2]))


def test_clean_duplicates_mean_aggregates_duplicate_pressure_rows() -> None:
    model_data = ModelData(
        pressure=np.array([2.0, 1.0, 1.0]),
        temperature=np.array([20.0, 10.0, 12.0]),
        salinity=np.array([35.2, 35.0, 35.4]),
    )

    cleaned = model_data.clean_duplicates(rule="mean")

    np.testing.assert_array_equal(cleaned.pressure, np.array([1.0, 2.0]))
    np.testing.assert_allclose(cleaned.temperature, np.array([11.0, 20.0]))
    np.testing.assert_allclose(cleaned.salinity, np.array([35.2, 35.2]))


def test_clean_duplicates_error_rule_rejects_non_increasing_pressure() -> None:
    model_data = ModelData(
        pressure=np.array([1.0, 1.0, 2.0]),
        temperature=np.array([10.0, 11.0, 20.0]),
        salinity=np.array([35.0, 35.1, 35.2]),
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        model_data.clean_duplicates(rule="error")


def test_clean_duplicates_rejects_unknown_rule() -> None:
    model_data = ModelData(
        pressure=np.array([1.0, 2.0]),
        temperature=np.array([10.0, 20.0]),
        salinity=np.array([35.0, 35.1]),
    )

    with pytest.raises(ValueError, match="Unknown duplicate_pressure policy"):
        model_data.clean_duplicates(rule="bad_rule")
