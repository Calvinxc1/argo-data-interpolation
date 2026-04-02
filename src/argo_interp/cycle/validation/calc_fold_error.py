import numpy as np
from typing import Any

from .InterleavedKFolds import InterleavedKFolds
from .calc_measure_error import calc_measure_error
from ..adapter import BaseAdapter
from ..model import ModelData


def calc_fold_error(model_data: ModelData, n_folds: int, adapter: BaseAdapter,
                    model_kwargs: dict[str, Any] = None) -> tuple[float, float]:
    n_obs = len(model_data.pressure)
    k_folds = InterleavedKFolds(n_obs, n_folds)

    temp_sse = 0
    sal_sse = 0
    valid_obs = 0
    for fold in range(n_folds):
        train_mask, valid_mask = k_folds.fold_mask(fold)
        train_pressure, valid_pressure = model_data.pressure[train_mask], model_data.pressure[valid_mask]
        train_temperature, valid_temperature = model_data.temperature[train_mask], model_data.temperature[valid_mask]
        train_salinity, valid_salinity = model_data.salinity[train_mask], model_data.salinity[valid_mask]

        temp_model = adapter.fit(pressure_data=train_pressure,
                                 measure_data=train_temperature,
                                 model_kwargs=model_kwargs)
        temp_sse += calc_measure_error(
            adapter=temp_model,
            pressure_data=valid_pressure,
            measure_data=valid_temperature,
        )

        sal_model = adapter.fit(pressure_data=train_pressure,
                                measure_data=train_salinity,
                                model_kwargs=model_kwargs)
        sal_sse += calc_measure_error(
            adapter=sal_model,
            pressure_data=valid_pressure,
            measure_data=valid_salinity,
        )

        valid_obs += len(valid_pressure)

    temp_sse = np.sqrt(temp_sse / valid_obs)
    sal_sse = np.sqrt(sal_sse / valid_obs)
    return temp_sse, sal_sse
