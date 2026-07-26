from __future__ import annotations

import numpy as np

from argo_interp.model import CycleData


def weighted_profile_mean(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    weight_sum = np.isfinite(values) @ weights
    weighted_sum = np.nansum(values * weights, axis=1)
    return np.divide(
        weighted_sum,
        weight_sum,
        out=np.full_like(weighted_sum, np.nan, dtype=float),
        where=weight_sum != 0,
    )


def weighted_profile_variance(variances: np.ndarray, weights: np.ndarray) -> np.ndarray:
    finite_mask = np.isfinite(variances)
    weight_sum = finite_mask @ weights

    alpha = np.divide(
        finite_mask * weights,
        weight_sum[:, np.newaxis],
        out=np.zeros_like(variances, dtype=float),
        where=weight_sum[:, np.newaxis] != 0,
    )

    weighted_variance = np.nansum(variances * alpha**2, axis=1)
    weighted_variance[weight_sum == 0] = np.nan
    return weighted_variance


def weighted_cycle_prediction(interpolates: CycleData, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return (
        weighted_profile_mean(interpolates.temperature.to_numpy(copy=False), weights),
        weighted_profile_mean(interpolates.salinity.to_numpy(copy=False), weights),
    )


def weighted_cycle_variance(interp_variance: CycleData, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return (
        weighted_profile_variance(interp_variance.temperature.to_numpy(copy=False), weights),
        weighted_profile_variance(interp_variance.salinity.to_numpy(copy=False), weights),
    )
