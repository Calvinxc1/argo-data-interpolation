from dataclasses import dataclass

import numpy as np
import xarray as xr

from argo_interp.cycle.config.ModelKwargs import ModelKwargs
from argo_interp.cycle.config.ModelSettings import ModelSettings
from argo_interp.cycle.domain.ModelData import ModelData
from argo_interp.cycle.validation.calc_fold_error import calc_fold_error
from argo_interp.data.data_filter import data_filter


@dataclass
class OffsetAdapter:
    offset: float = 0.0

    @classmethod
    def fit(
        cls,
        pressure_data: np.ndarray,
        measure_data: np.ndarray,
        model_kwargs: dict[str, float],
    ) -> "OffsetAdapter":
        del pressure_data, measure_data
        return cls(offset=model_kwargs.get("offset", 0.0))

    def interpolate(self, pressure_data: np.ndarray) -> np.ndarray:
        return np.asarray(pressure_data, dtype=float) + self.offset


def test_calc_fold_error_returns_rmse_for_each_measure() -> None:
    model_data = ModelData(
        pressure=np.array([0.0, 1.0, 2.0, 3.0]),
        temperature=np.array([1.0, 2.0, 3.0, 4.0]),
        salinity=np.array([10.0, 11.0, 12.0, 13.0]),
    )
    settings = ModelSettings(
        n_folds=2,
        model_kwargs=ModelKwargs(temperature={"offset": 1.0}, salinity={"offset": -2.0}),
    )

    temp_error, sal_error = calc_fold_error(model_data, OffsetAdapter, settings)

    np.testing.assert_allclose(temp_error, 1.0)
    np.testing.assert_allclose(sal_error, 12.0)


def test_data_filter_combines_masks_and_drops_rows() -> None:
    dataset = xr.Dataset(
        data_vars={"temperature": ("obs", [10.0, 20.0, 30.0])},
        coords={"obs": [0, 1, 2]},
    )

    filtered = data_filter(
        dataset,
        [
            xr.DataArray([True, True, False], dims=["obs"]),
            xr.DataArray([False, True, True], dims=["obs"]),
        ],
    )

    np.testing.assert_array_equal(filtered.obs.values, np.array([1]))
    np.testing.assert_array_equal(filtered.temperature.values, np.array([20.0]))
