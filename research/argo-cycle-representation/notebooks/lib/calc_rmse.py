from numpy import pow, sqrt
from numpy.typing import ArrayLike


def calc_rmse(actual_vals: ArrayLike, predict_vals: ArrayLike) -> float:
    error = actual_vals - predict_vals
    mse_val = pow(error, 2).mean()
    rmse_val = sqrt(mse_val)
    return rmse_val
