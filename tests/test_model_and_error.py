from dataclasses import dataclass

import numpy as np

from argo_interp.cycle.model.Model import Model
from argo_interp.cycle.model.ModelAdapters import ModelAdapters
from argo_interp.cycle.config.ModelKwargs import ModelKwargs
from argo_interp.cycle.config.ModelSettings import ModelSettings
from argo_interp.cycle.config.SensorAccuracy import SensorAccuracy
from argo_interp.cycle.domain.CycleError import CycleError
from argo_interp.cycle.domain.MeasureError import MeasureError
from argo_interp.cycle.domain.ModelData import ModelData
from argo_interp.cycle.domain.ModelMeta import ModelMeta
from argo_interp.cycle.validation.calc_measure_error import calc_measure_error


@dataclass
class StubAdapter:
    offset: float = 0.0
    slope: float = 0.0

    def interpolate(self, pressure_data: np.ndarray) -> np.ndarray:
        pressure = np.asarray(pressure_data, dtype=float)
        return pressure + self.offset

    def gradient(self, pressure_data: np.ndarray) -> np.ndarray:
        pressure = np.asarray(pressure_data, dtype=float)
        return np.full_like(pressure, self.slope, dtype=float)

    @classmethod
    def fit(
        cls,
        pressure_data: np.ndarray,
        measure_data: np.ndarray,
        model_kwargs: dict[str, float],
    ) -> "StubAdapter":
        del pressure_data, measure_data
        return cls(**model_kwargs)


def test_calc_measure_error_returns_sum_of_squared_residuals() -> None:
    adapter = StubAdapter(offset=1.0)
    pressure = np.array([1.0, 2.0, 3.0])
    measure = np.array([3.0, 4.0, 5.0])

    error = calc_measure_error(adapter, pressure, measure)

    assert error == 3.0


def test_model_measure_error_combines_all_error_sources() -> None:
    measure_error = MeasureError(sensor=0.4, model=0.3)
    gradient = np.array([2.0, -1.0])

    result = Model._measure_error(pressure_error=0.5, measure_error=measure_error, measure_gradient=gradient)

    expected = np.sqrt(0.3**2 + 0.4**2 + np.array([1.0, 0.5]) ** 2)
    np.testing.assert_allclose(result, expected)


def test_model_interpolate_returns_model_data() -> None:
    model = Model(
        meta=_meta(),
        adapters=ModelAdapters(
            temperature=StubAdapter(offset=1.0),
            salinity=StubAdapter(offset=10.0),
        ),
        error=CycleError(
            pressure=1.0,
            temperature=MeasureError(sensor=0.2, model=0.1),
            salinity=MeasureError(sensor=0.3, model=0.2),
        ),
        settings=ModelSettings(n_folds=2),
    )

    pressure = np.array([1.0, 2.0])
    result = model.interpolate(pressure)

    np.testing.assert_array_equal(result.pressure, pressure)
    np.testing.assert_array_equal(result.temperature, np.array([2.0, 3.0]))
    np.testing.assert_array_equal(result.salinity, np.array([11.0, 12.0]))


def test_model_interp_error_uses_gradients_and_stored_error_values() -> None:
    model = Model(
        meta=_meta(),
        adapters=ModelAdapters(
            temperature=StubAdapter(slope=2.0),
            salinity=StubAdapter(slope=3.0),
        ),
        error=CycleError(
            pressure=0.5,
            temperature=MeasureError(sensor=0.4, model=0.3),
            salinity=MeasureError(sensor=0.2, model=0.1),
        ),
        settings=ModelSettings(n_folds=2),
    )

    pressure = np.array([1.0, 2.0])
    result = model.interp_error(pressure)

    np.testing.assert_array_equal(result.pressure, pressure)
    np.testing.assert_allclose(result.temperature, np.full(2, np.sqrt(0.3**2 + 0.4**2 + 1.0**2)))
    np.testing.assert_allclose(result.salinity, np.full(2, np.sqrt(0.1**2 + 0.2**2 + 1.5**2)))


def test_model_build_uses_cross_validated_errors_and_fitted_adapters() -> None:
    model_data = ModelData(
        pressure=np.array([0.0, 1.0, 2.0, 3.0]),
        temperature=np.array([1.0, 2.0, 3.0, 4.0]),
        salinity=np.array([10.0, 11.0, 12.0, 13.0]),
    )
    settings = ModelSettings(
        n_folds=2,
        model_kwargs=ModelKwargs(temperature={"offset": 1.5, "slope": 0.25}, salinity={"offset": -2.0, "slope": 0.75}),
        sensor_accuracy=SensorAccuracy(pressure=0.6, temperature=0.05, salinity=0.08),
    )

    model = Model.build(_meta(), model_data, StubAdapter, settings)

    assert model.error.pressure == 0.6
    assert model.error.temperature.sensor == 0.05
    assert model.error.salinity.sensor == 0.08
    np.testing.assert_allclose(model.error.temperature.model, 0.5)
    np.testing.assert_allclose(model.error.salinity.model, 12.0)

    np.testing.assert_array_equal(model.interpolate(np.array([1.0])).temperature, np.array([2.5]))
    np.testing.assert_array_equal(model.interpolate(np.array([1.0])).salinity, np.array([-1.0]))


def _meta() -> ModelMeta:
    return ModelMeta(
        cycle_id="cycle-1",
        latitude=1.0,
        longitude=2.0,
        timestamp=np.datetime64("2026-01-01"),
        profile_pressure=(0.0, 100.0),
    )
