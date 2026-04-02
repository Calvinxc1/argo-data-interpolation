import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class InterleavedKFolds:
    n_obs: int
    n_folds: int
    keep_start: bool = True
    keep_end: bool = True
    folds: NDArray[np.int_] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        fold_start_idx = int(self.keep_start)
        fold_end_idx = self.n_obs - int(self.keep_end)
        fold_idx = np.arange(fold_start_idx, fold_end_idx)

        folds = np.full(self.n_obs, -1, dtype=int)
        folds[fold_idx] = np.arange(fold_end_idx - fold_start_idx) % self.n_folds
        object.__setattr__(self, "folds", folds)

    def fold_mask(self, fold: int) -> tuple[NDArray[np.bool_], NDArray[np.bool_]]:
        valid_mask = self.folds == fold
        train_mask = np.logical_not(valid_mask)
        return train_mask, valid_mask

    def fold_index(self, fold: int) -> tuple[NDArray[np.int_], NDArray[np.int_]]:
        idx = np.arange(self.n_obs)
        train_mask, valid_mask = self.fold_mask(fold)
        train_idx = idx[train_mask]
        valid_idx = idx[valid_mask]
        return train_idx, valid_idx
