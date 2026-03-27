import pickle

import numpy as np
import pytest
from scipy.interpolate import BSpline

from argo_interp.cycle import CycleError, CycleModel, CycleSettings, ModelError, SensorError


def _example_spline(offset: float = 0.0) -> BSpline:
    knots = np.array([0.0, 0.0, 0.0, 0.0, 10.0, 10.0, 10.0, 10.0])
    coeffs = np.array([0.0, 1.0, 2.0, 3.0]) + offset
    return BSpline(knots, coeffs, 3)


def _example_cycle_model() -> CycleModel:
    return CycleModel(
        temperature=_example_spline(),
        salinity=_example_spline(offset=0.5),
        error=CycleError(
            model=ModelError(temperature=0.1, salinity=0.01),
            sensor=SensorError(),
        ),
        settings=CycleSettings(
            prominence=0.25,
            window=5,
            spacing=5.0,
            peak_dist=20,
            folds=5,
        ),
        pressure_bounds=(0.0, 10.0),
    )


def test_cycle_model_interpolate_returns_expected_columns() -> None:
    cycle_model = _example_cycle_model()

    interpolation = cycle_model.interpolate(np.array([0.0, 5.0, 10.0]))

    assert list(interpolation.columns) == [
        "temperature",
        "salinity",
        "temp_error",
        "sal_error",
    ]
    assert list(interpolation.index) == [0.0, 5.0, 10.0]


def test_cycle_model_rejects_queries_outside_pressure_bounds() -> None:
    cycle_model = _example_cycle_model()

    with pytest.raises(ValueError, match="pressure_values"):
        cycle_model.interpolate(np.array([-0.1, 5.0]))


def test_cycle_model_pickle_round_trip_preserves_results() -> None:
    cycle_model = _example_cycle_model()
    query = np.array([1.0, 5.0, 9.0])

    restored = pickle.loads(pickle.dumps(cycle_model))

    np.testing.assert_allclose(
        cycle_model.interpolate(query).to_numpy(),
        restored.interpolate(query).to_numpy(),
    )


def test_cycle_model_state_round_trip_preserves_results() -> None:
    cycle_model = _example_cycle_model()
    query = np.array([1.0, 5.0, 9.0])

    restored = CycleModel.from_state(cycle_model.to_state())

    assert restored.settings == cycle_model.settings
    assert restored.error == cycle_model.error
    assert restored.pressure_bounds == cycle_model.pressure_bounds
    np.testing.assert_allclose(
        cycle_model.interpolate(query).to_numpy(),
        restored.interpolate(query).to_numpy(),
    )


def test_cycle_model_from_state_rejects_unknown_version() -> None:
    cycle_model = _example_cycle_model()
    state = cycle_model.to_state()
    invalid_state = (999, *state[1:])

    with pytest.raises(ValueError, match="Unsupported CycleModel state version"):
        CycleModel.from_state(invalid_state)
