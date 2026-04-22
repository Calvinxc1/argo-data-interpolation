from __future__ import annotations

import numpy as np

from argo_interp.model import CycleData


def weighted_profile_mean(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    weight_sum = np.isfinite(values) @ weights
    weighted_sum = np.nansum(values * weights, axis=1)
    return weighted_sum / weight_sum


def weighted_cycle_prediction(interpolates: CycleData, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return (
        weighted_profile_mean(interpolates.temperature.to_numpy(copy=False), weights),
        weighted_profile_mean(interpolates.salinity.to_numpy(copy=False), weights),
    )
