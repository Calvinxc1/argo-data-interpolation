import pandas as pd
import numpy as np

from .CycleSettings import CycleSettings
from .build_model import build_model
from .calc_rmse import calc_rmse


def calc_fold_error(cycle_data: pd.DataFrame, settings: CycleSettings) -> tuple[float, float]:
    fold_obs_idx = np.arange(1, len(cycle_data) - 1)
    folds_idx = np.array([-1, *((fold_obs_idx - 1) % settings.folds), -1])

    valid_obs = 0
    rmse_temp = 0
    rmse_sal = 0
    for fold in range(settings.folds):
        valid_mask = folds_idx == fold
        train_data = cycle_data.loc[~valid_mask]
        valid_data = cycle_data.loc[valid_mask]

        model_temp = build_model(train_data['PRES'], train_data['TEMP'], settings)
        predict_temp = model_temp(valid_data['PRES'])
        rmse_temp += calc_rmse(valid_data['TEMP'], predict_temp) * len(valid_data)

        model_sal = build_model(train_data['PRES'], train_data['PSAL'], settings)
        predict_sal = model_sal(valid_data['PRES'])
        rmse_sal += calc_rmse(valid_data['PSAL'], predict_sal) * len(valid_data)

        valid_obs += len(valid_data)
    rmse_temp /= valid_obs
    rmse_sal /= valid_obs
    return rmse_temp, rmse_sal
