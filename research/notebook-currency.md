# Notebook Currency

The notebooks under each topic's `notebooks/` folder are a research record of
experiments as they were run. They are not maintained as a working example
suite for the current package, and parts of them have fallen behind the code.
This note records what is current, what is not, and what that means when
reading them.

The package under `src/argo_kwsi/` is the source of truth for the method. Where
a notebook and the package disagree, the package is correct.

## What is current

Every notebook's import statements were updated when the package was renamed to
`argo_kwsi`, and all of those imports resolve against the current package. The
notebook source is syntactically current and the module paths are correct.

## What is not current

### Recorded cell outputs

Cell outputs stored in the tracked `.ipynb` files come from earlier runs and
have not been regenerated. They carry checkout paths that no longer exist, and
tracebacks and warnings that name the pre-rename module layout. Those outputs
are left as they were recorded rather than edited, because rewriting them would
misrepresent what those runs actually printed.

Read the outputs as a historical record of a specific run, not as the result of
running the current code. Re-run a notebook before citing any number from its
stored output.

### Notebooks 01 and 02 under `argo-cycle-representation`

These two predate the packaged cycle API and still import
`CycleModel`, `CycleSettings`, `ModelError` and `SensorError` from
[argo-cycle-representation/notebooks/lib](argo-cycle-representation/notebooks/lib).
Those classes were superseded in the package by `Model`, `ModelSettings`,
`MeasureError` and `SensorAccuracy`. The local copies are kept so the notebooks
still run as recorded; they are not the current architecture, and
[03-cycle-representation-comparisons.py](argo-cycle-representation/notebooks/03-cycle-representation-comparisons.py)
is the first notebook in that topic to use the packaged API.

### Research-local helpers that the package has since absorbed

[underwater-acoustics/notebooks/lib](underwater-acoustics/notebooks/lib)
re-implements names that now live in `argo_kwsi.uncertainty`, among them
`GaussianScale`, `WeightConfig`, `WeightDeltas`, `WeightComponents`,
`AVERAGE_YEAR_SECONDS`, `CandidateQuery`, `build_candidate_query`,
`compute_weight_deltas`, `season_fraction`, `seasonal_distance_seconds`,
`weighted_cycle_prediction`, `weighted_profile_mean` and
`weighted_profile_variance`.

These local copies do not receive package fixes. A notebook importing them can
therefore produce a different answer than the same call through
`argo_kwsi.uncertainty`. One known instance: the package's
`weighted_profile_mean` excludes every non-finite value from its numerator, so
numerator and denominator agree on which entries count as supported, while the
`lib` copy sums with `np.nansum`, which drops `NaN` but propagates infinities.

Prefer the packaged API for new work. Treat the `lib` copies as frozen research
support for the runs that already used them.

## License

This file is part of the [`research/`](README.md) subtree and is licensed under
the Creative Commons Attribution 4.0 International license. See
[`LICENSE`](LICENSE).
