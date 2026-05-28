from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class InterleavedKFolds:
    n_obs: int
    n_folds: int
    keep_start: bool = True
    keep_end: bool = True
    folds: NDArray[np.int_] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.n_obs < 1:
            raise ValueError("n_obs must be at least 1")
        if self.n_folds < 1:
            raise ValueError("n_folds must be at least 1")

        fold_start_idx = int(self.keep_start)
        fold_end_idx = self.n_obs - int(self.keep_end)
        n_validation_obs = fold_end_idx - fold_start_idx
        if n_validation_obs < 1:
            raise ValueError(
                "at least one validation observation is required after endpoint reservation"
            )
        if self.n_folds > n_validation_obs:
            raise ValueError("n_folds cannot exceed available validation observations")

        fold_idx = np.arange(fold_start_idx, fold_end_idx)

        folds = np.full(self.n_obs, -1, dtype=int)
        folds[fold_idx] = np.arange(n_validation_obs) % self.n_folds
        object.__setattr__(self, "folds", folds)

    def fold_mask(self, fold: int) -> tuple[NDArray[np.bool_], NDArray[np.bool_]]:
        if fold < 0 or fold >= self.n_folds:
            raise ValueError("fold must be between 0 and n_folds - 1")

        valid_mask = self.folds == fold
        train_mask = np.logical_not(valid_mask)
        return train_mask, valid_mask

    def fold_index(self, fold: int) -> tuple[NDArray[np.int_], NDArray[np.int_]]:
        idx = np.arange(self.n_obs)
        train_mask, valid_mask = self.fold_mask(fold)
        train_idx = idx[train_mask]
        valid_idx = idx[valid_mask]
        return train_idx, valid_idx
