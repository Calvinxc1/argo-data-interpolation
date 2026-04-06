import numpy as np

from argo_interp.cycle.adapter import LinearAdapter, PchipAdapter, SplineAdapter


def test_linear_adapter_reproduces_linear_data_and_gradient() -> None:
    pressure = np.array([0.0, 1.0, 2.0, 3.0])
    measure = 2.0 * pressure + 1.0

    adapter = LinearAdapter.fit(pressure, measure, model_kwargs={})

    np.testing.assert_allclose(adapter.interpolate(pressure), measure)
    np.testing.assert_allclose(adapter.gradient(np.array([0.5, 1.5])), np.array([2.0, 2.0]))


def test_pchip_adapter_reproduces_training_points_and_disables_extrapolation() -> None:
    pressure = np.array([0.0, 1.0, 2.0, 3.0])
    measure = np.array([0.0, 1.0, 4.0, 9.0])

    adapter = PchipAdapter.fit(pressure, measure, model_kwargs={})

    np.testing.assert_allclose(adapter.interpolate(pressure), measure)
    outside = adapter.interpolate(np.array([-1.0, 4.0]))
    assert np.isnan(outside).all()


def test_spline_adapter_returns_finite_values_for_smooth_input() -> None:
    pressure = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    measure = pressure**2

    adapter = SplineAdapter.fit(pressure, measure, model_kwargs={"k": 3})

    values = adapter.interpolate(np.array([0.5, 1.5, 2.5]))
    gradient = adapter.gradient(np.array([0.5, 1.5, 2.5]))

    assert values.shape == (3,)
    assert gradient.shape == (3,)
    assert np.isfinite(values).all()
    assert np.isfinite(gradient).all()
