import numpy as np

from argo_interp.cycle.validation.InterleavedKFolds import InterleavedKFolds


def test_interleaved_kfolds_reserves_endpoints_by_default() -> None:
    folds = InterleavedKFolds(n_obs=8, n_folds=3)

    np.testing.assert_array_equal(folds.folds, np.array([-1, 0, 1, 2, 0, 1, 2, -1]))


def test_fold_mask_returns_complementary_masks() -> None:
    folds = InterleavedKFolds(n_obs=8, n_folds=3)

    train_mask, valid_mask = folds.fold_mask(1)

    assert np.all(~valid_mask == train_mask)
    np.testing.assert_array_equal(np.flatnonzero(valid_mask), np.array([2, 5]))


def test_fold_index_matches_fold_mask() -> None:
    folds = InterleavedKFolds(n_obs=8, n_folds=3)

    train_idx, valid_idx = folds.fold_index(2)

    np.testing.assert_array_equal(valid_idx, np.array([3, 6]))
    np.testing.assert_array_equal(train_idx, np.array([0, 1, 2, 4, 5, 7]))


def test_interleaved_kfolds_handles_small_observation_count() -> None:
    folds = InterleavedKFolds(n_obs=2, n_folds=5)

    np.testing.assert_array_equal(folds.folds, np.array([-1, -1]))
