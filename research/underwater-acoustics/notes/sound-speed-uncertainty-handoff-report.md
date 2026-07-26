# Sound-Speed Uncertainty Handoff Report

Date: 2026-07-25 PDT
Tracker: Kanboard `#159`, "OCEANS 2026 paper: technical deliverables (Coding Agent handoff)"
Status: paused by Jason, PR open but intentionally not merged

This report maps the Education handoff items to the current repository state.
It is intentionally shorter than the implementation log in
[`sound-speed-uncertainty-implementation-plan.md`](sound-speed-uncertainty-implementation-plan.md).

## Paused State

Paused on 2026-07-25 PDT / 2026-07-26 UTC after completing the brief 3
validation rerun and pushing branch `feature/uncertainty-estimation`.

Repository state to resume from:

- Current branch: `feature/uncertainty-estimation`
- Latest pushed commit: `1df8c98 feat: add out-of-sample calibration split`
- Open PR: `#14`, `feature/uncertainty-estimation` into `dev`,
  <https://github.com/Calvinxc1/argo-data-interpolation/pull/14>
- PR merge state: intentionally unmerged; Jason asked to table the work before
  merging.
- Tracked worktree state after the pushed validation commit was clean. A local
  generated `research/underwater-acoustics/notebooks/lib/__pycache__/` may be
  present and should not be treated as project work.

Completed before pause:

- Notebook `6` product, benchmark outputs, and finalized `110` dbar/m contour
  charts are generated from cache.
- Full four-depth notebook `6` hold-one-float-out validation exists.
- Matched replication-grid validation exists on `5..500 m` at `1 m` spacing
  with notebook `6`, distance-only, and flat Jana-style predictors.
- The out-of-sample calibration split exists with fixed seed `20260725`.
- The distance-only kernel ablation exists in the same harness.
- Runtime notes identify Jason's `galatea` system as the execution host.

Most important local generated outputs:

- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_predictor_summary.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_sigma_coverage.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_coverage_curve.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_platform_split.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_metadata.json`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_detail.csv`

Headline resume facts:

- Matched replication-grid run completed in `3,217.54` seconds (`53:37.54`) on
  `galatea`.
- It evaluated `20,779` held-out cycles, skipped `207` low-support cycles, and
  wrote `10,306,384` detail rows.
- Notebook `6` won p75 per-cycle RMSE for temperature, salinity, and TEOS-10
  sound speed over both the flat Jana-style predictor and the distance-only
  ablation.
- Distance-only did not improve over the flat baseline in this harness, so the
  accuracy gain should be framed as coming from the temporal and seasonal
  weighting stack.
- Notebook `6` TEOS-10 sound-speed `with_spatial` 2-sigma coverage was
  `95.09%` in sample and `95.06%` out-of-sample pooled, against `95.45%`
  nominal.
- The `no_spatial` TEOS-10 coverage remained much too narrow at `5.49%`,
  `10.87%`, and `16.01%` for 1, 2, and 3 sigma.

Likely next step when resumed: decide how to integrate the validation and
calibration wording into the OCEANS paper and whether PR `#14` should be
reviewed, amended, or merged into `dev`. Do not merge without a fresh Jason
approval.

## Current Product State

Notebook `6-sound-speed-uncertainty-product` is the current paper-support
pipeline. It uses the cached PCHIP cycle-model bundle, propagates
temperature/salinity variance through GSW / TEOS-10 sound speed, and writes a
query-point table with componentized variance buckets.

Current cached configuration:

- anchor date: `2015-07-01`
- target pressures: `5`, `35`, `110`, and `500` dbar
- horizontal grid: `0.1` degree
- distance kernel sigma: `1/3` degree
- hard candidate prefilter: `3 sigma`, `dist_rad = 1.0` degree
- temporal weighting: enabled
- wrapped seasonal weighting: enabled
- T-S covariance: set to zero; no cross term included
- TEOS-10 formula uncertainty floor: not folded into reported sigma

Current cached outputs:

- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_product.pkl`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_product.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_product_110m.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_depth_summary.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_benchmark.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_benchmark_metadata.json`
- `research/underwater-acoustics/notebooks/data/charts/sound_speed_teos10_110m.{png,svg}`
- `research/underwater-acoustics/notebooks/data/charts/sigma_sound_speed_teos10_110m.{png,svg}`
- `research/underwater-acoustics/notebooks/data/charts/w_raw_110m.{png,svg}`
- `research/underwater-acoustics/notebooks/data/charts/sound_speed_teos10_w_contours_110m.{png,svg}`
- `research/underwater-acoustics/notebooks/data/charts/sigma_sound_speed_teos10_w_contours_110m.{png,svg}`

The full product currently has `92,308` rows and `39` columns, with `23,077`
rows at each target pressure. At `110` dbar, `22,636` of `23,077` rows have
finite propagated sound-speed sigma. The `110` dbar sigma `p01..p99` range is
approximately `4.1629..5.3442 m/s`.

## Must-Have Mapping

Sound-speed uncertainty propagation is implemented for the TEOS-10 path. The
propagation uses the GUM delta-method simplification
`var_c = (dc/dT)^2 var_T + (dc/dS)^2 var_S`; `cov_TS = 0` by scoped decision.
The older EOS-80 path is not implemented in notebook `6`; the current
implementation intentionally avoids the deprecated `seawater` path. Jason
confirmed on 2026-07-25 that TEOS-10-only is sufficient for the current
paper-support scope.

Depth-resolved reporting is now explicit through the full product table and
`sound_speed_uncertainty_depth_summary.csv`. The current summary has one row
per target pressure and reports row counts, finite sigma counts, sigma
quantiles, support medians, and effective/candidate cycle-count medians.

The spatiotemporal rerun is complete for the current paper-support
configuration. Product metadata confirms `use_time_weight = true` and
`use_season_weight = true`.

Full hold-one-float-out validation has now been run under the final notebook
`6` configuration. The run uses the cached PCHIP cycle-model bundle, predicts
each held-out cycle at the four notebook `6` target pressures from neighboring
cycles while excluding the held-out platform, and applies the final
distance/time/season Gaussian weights. It writes:

- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_summary.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_metadata.json`

The run evaluated `20,982` cycles at each target pressure, skipped `4` cached
cycles with no non-platform candidate support, and wrote `83,928` detail rows.
At `110` dbar, finite validation counts are `20,570` and TEOS-10 sound-speed
error metrics are RMSE `4.6891 m/s`, MAE `3.5827 m/s`, and bias `0.1588 m/s`.

The five immediate `110` dbar figures are generated. The sound-speed point
estimate chart and the sound-speed-with-contours chart now share the same
custom sound-speed colormap. Both support-overlay figures use
`W_raw = 6` and `W_raw = 30` contours; no finalized support-overlay chart uses
W opacity.

Variance-space contribution decomposition exists in the product columns:

- T/S sensor precision variance
- T/S pressure-gradient variance
- T/S vertical-model variance
- T/S spatial variance
- propagated sound-speed contribution columns for each bucket
- propagated sound-speed sensor bucket
- propagated sound-speed model bucket

The requested per-cycle and per-float decomposition is future work for the
package rather than a current paper blocker. The product stores aggregate
candidate counts, support weights, and effective counts at each query
point/depth; it does not export a separate per-cycle or per-float contribution
table.

Approach A is the current production configuration. The product uses fixed
scales: distance sigma `1/3` degree, year stdev `3`, seasonal window `8` weeks,
and seasonal border stdev `3` weeks. Approach C, depth-varying scales, is future
work rather than a current paper blocker.

The cached-input benchmark output is complete for the current paper-support
scope. The notebook writes:

- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_benchmark.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_benchmark_metadata.json`

This benchmark covers the cached cycle-model plus cached spatial-variance
product-build path across `1.0`, `0.5`, `0.25`, and `0.1` degree grid steps and
one-versus-four target-pressure cases. The production `0.1` degree, four-depth
case produced `92,308` rows, `90,362` finite sigma rows, `173.80` seconds of
measured row-construction wall time, `48.10` seconds of one-time cycle-target
precompute time, and `151.999` MB of peak traced Python memory. These runtime
figures were measured on Jason's `galatea` system. The benchmark does not
measure raw Argo download, cycle-model rebuild, or spatial-variance
recomputation.

Historical runtime observations for full recomputation remain useful context:

- `3 sigma` candidate prefilter on `galatea`: spatial validation about `4:15`,
  gridded product build about `1:14`
- `6 sigma` candidate prefilter on `galatea`: spatial validation about `12:00`,
  gridded product build about `1:45`

Reproducibility hardening is partial. The notebook now has cache metadata guards
for weighting configuration changes, Jupytext pairing, and saved output paths.
Pinned rerun steps are below, but dependency lock/pin discipline has not been
expanded beyond the current project environment.

## Benchmark Output

The current benchmark separates three costs that the notebook can otherwise
combine:

- per-cycle model bundle rebuild from raw Argo data;
- depthwise spatial-variance validation;
- gridded query-product build from cached cycle models and spatial variance.

For the paper-support deadline, the useful measured path is the cached-input
path, because that is the path used for figure iteration. The benchmark records:

- configuration metadata: grid step, query-point count, pressure count,
  candidate radius, temporal switches, and seasonal switches;
- wall time for precomputing target-pressure cycle arrays;
- wall time for query-product row construction;
- peak traced Python memory;
- output row count and finite-sigma count;
- Python, NumPy, pandas, GSW, and Cartopy versions.

Current measured matrix:

| Case | Grid step | Pressures | Rows | Finite sigma | Wall time seconds | Peak traced MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `grid_1p0_depth1` | `1.0` | `1` | `241` | `231` | `1.61` | `0.86` |
| `grid_1p0_depth4` | `1.0` | `4` | `964` | `938` | `1.76` | `1.86` |
| `grid_0p5_depth1` | `0.5` | `1` | `930` | `902` | `5.84` | `1.76` |
| `grid_0p5_depth4` | `0.5` | `4` | `3,720` | `3,654` | `6.84` | `6.33` |
| `grid_0p25_depth4` | `0.25` | `4` | `14,868` | `14,581` | `27.55` | `24.62` |
| `grid_0p1_depth4` | `0.1` | `4` | `92,308` | `90,362` | `173.80` | `152.00` |

## Holdout Validation Output

The current notebook `6` hold-one-float-out validation is a predictive
validation of the final paper-support weighting configuration, not just the
internal spatial-variance residual pass. For each cached PCHIP cycle model, it:

- targets the held-out cycle's own PCHIP estimate at `5`, `35`, `110`, and
  `500` dbar;
- excludes all cycles from the held-out `PLATFORM_NUMBER`;
- uses the final hard spatial prefilter, `dist_rad = 1.0` degree;
- applies final distance, absolute-time, and wrapped-season Gaussian weights;
- computes temperature, salinity, and TEOS-10 sound-speed errors.

Summary metrics:

| Pressure dbar | Finite sound-speed count | Temperature RMSE | Salinity RMSE | Sound-speed RMSE | Sound-speed MAE | Sound-speed bias |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `5` | `15,774` | `0.6077` | `0.6859` | `1.6216` | `1.1154` | `0.1086` |
| `35` | `20,862` | `0.7821` | `0.4541` | `1.7362` | `1.2061` | `0.0306` |
| `110` | `20,570` | `1.7994` | `0.1566` | `4.6891` | `3.5827` | `0.1588` |
| `500` | `15,951` | `0.2073` | `0.0410` | `0.7543` | `0.5790` | `0.0144` |

## Matched Replication-Grid Holdout Validation

The 2026-07-25 rerun removes the old statistic/depth-grid confounds by running
both the notebook `6` spatiotemporal Gaussian predictor and a flat Jana-style
predictor through the same harness, same held-out cycles, same depth levels,
and same aggregation.

Generated outputs:

- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_detail.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_cycle_summary.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_predictor_summary.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_depth_summary.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_sigma_coverage.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_coverage_curve.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_platform_split.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_spatial_variance.csv`
- `research/underwater-acoustics/notebooks/data/sound_speed_uncertainty_holdout_validation_replication_grid_metadata.json`

Design details:

- Depth grid is `5` to `500` m inclusive at `1` m spacing, `496` levels.
- The grid is represented in metres. For each held-out cycle, the script
  converts each `depth_m` to `pressure_dbar` with
  `gsw.p_from_z(-depth_m, cycle_latitude)` before interpolating that cycle's
  PCHIP model.
- Withholding is hold-one-float-out: all cycles from the held-out
  `PLATFORM_NUMBER` are excluded for both predictors.
- The shared predictor candidate set is the same 2 degree by 2 degree spatial
  window, with cycles skipped for both predictors when the shared candidate
  count is below `min_cycles = 30`.
- NaN rule: per-cycle RMSE/MAE use only finite depth-level errors for that
  cycle, predictor, and variable. The detail file keeps each cycle/depth row,
  and the cycle summary reports finite level counts.
- The rerun evaluated `20,779` held-out cycles on the full depth grid and
  skipped `207` cycles for low support. The predictor summary has `20,772`
  valid per-cycle metric rows after finite-error filtering. The detail output
  contains `10,306,384` rows.
- Runtime on Jason's `galatea` system was `3,217.54` seconds (`53:37.54`) for
  the matched validation run from cached PCHIP cycle models, including the
  same-run notebook `6` spatial-variance pass, three predictors, out-of-sample
  calibration split summaries, detail CSV streaming, summary CSVs, coverage
  curve CSV, and metadata JSON.
- The follow-up notebook `6` Python-export rerender for the finalized chart
  files completed on `galatea` in `16.77` seconds from existing caches.
- The calibration split uses seed `20260725` and partitions floats by
  `PLATFORM_NUMBER`: group A has `74` floats and `10,790` cycles; group B has
  `73` floats and `10,196` cycles. The split controls only which residuals
  estimate the spatial variance bucket; LOFO predictions still use the full
  archive minus the held-out platform.

Headline per-cycle p75 RMSE comparison:

| Variable | Notebook 6 p75 RMSE | Distance-only p75 RMSE | Flat Jana-style p75 RMSE | Notebook 6 vs flat | Winner |
| --- | ---: | ---: | ---: | ---: | --- |
| Temperature | `1.0500 deg C` | `1.3628 deg C` | `1.3419 deg C` | `-21.75%` | Notebook 6 |
| Salinity | `0.2402 PSU` | `0.2755 PSU` | `0.2747 PSU` | `-12.58%` | Notebook 6 |
| TEOS-10 sound speed | `2.8258 m/s` | `3.6133 m/s` | `3.5719 m/s` | `-20.89%` | Notebook 6 |

The paper-facing statement supported by this run is that, under matched
cycles, matched metre-grid levels, and matched per-cycle p75 RMSE aggregation,
the notebook `6` spatiotemporal Gaussian predictor outperformed both the flat
Jana-style predictor and the distance-only ablation for temperature, salinity,
and TEOS-10 sound speed. The distance-only ablation did not improve over the
flat baseline in this matched harness, so the measured gain should be
attributed to the temporal and seasonal weighting stack rather than to the
distance kernel alone.

Sigma coverage is reported for two variants: `no_spatial`, which includes only
the propagated sensor, pressure, and vertical interpolation/model terms, and
`with_spatial`, which also includes the depthwise spatial residual variance
bucket. The output now reports both the original in-sample consistency check
and an out-of-sample calibration split. In the out-of-sample rows, group A
residuals estimate the spatial bucket tested on group B, and group B residuals
estimate the spatial bucket tested on group A.

Notebook `6` pooled coverage:

| Scope | Variable | Sigma variant | Count | Within 1 sigma | Within 2 sigma | Within 3 sigma | Mean 2-sigma width |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| In sample | Temperature | with spatial | `8,910,082` | `73.34%` | `94.99%` | `99.01%` | `3.0972 deg C` |
| Out of sample pooled | Temperature | with spatial | `8,910,082` | `73.32%` | `94.96%` | `99.00%` | `3.0961 deg C` |
| In sample | Salinity | with spatial | `8,910,082` | `88.10%` | `96.87%` | `98.80%` | `0.5418 PSU` |
| Out of sample pooled | Salinity | with spatial | `8,910,082` | `86.70%` | `96.60%` | `98.65%` | `0.5402 PSU` |
| In sample | TEOS-10 sound speed | with spatial | `8,910,082` | `73.49%` | `95.09%` | `99.03%` | `8.8121 m/s` |
| Out of sample pooled | TEOS-10 sound speed | with spatial | `8,910,082` | `73.48%` | `95.06%` | `99.02%` | `8.8131 m/s` |
| In sample | TEOS-10 sound speed | no spatial | `8,910,082` | `5.49%` | `10.87%` | `16.01%` | `0.4135 m/s` |
| Out of sample pooled | TEOS-10 sound speed | no spatial | `8,910,082` | `5.49%` | `10.87%` | `16.01%` | `0.4135 m/s` |

The `no_spatial` coverage is intentionally poor for temperature and sound
speed, showing that local propagated instrument/interpolation terms alone do
not explain realized holdout errors. The spatial bucket is therefore central
to the product's reported sigma. For TEOS-10 sound speed, out-of-sample pooled
`with_spatial` 2-sigma coverage is `95.06%` against the nominal normal
expectation of `95.45%`; the in-sample value is `95.09%`, so the split has
negligible effect on the headline calibration result. Median predictive
interval widths in the coverage CSV are histogram-based approximations.

## Approach A / C Feasibility

Approach A, fixed mesoscale-inspired scales, is already the implemented floor.
The current fixed scales are simple to describe and already produced the
paper-support product.

Approach C, depth-varying scales, is feasible but not a small isolated change
inside the current notebook. The spatial candidate query, cache metadata,
spatial-variance validation, and product row builder all assume one shared
horizontal radius for all target depths. A depth-varying implementation would
need either:

- a per-depth candidate/support pass inside each query point, increasing
  product-build work roughly with pressure count; or
- grouped depth bands with shared radii, which is cheaper but requires a
  paper-defensible rule for the band boundaries and scale values.

Recommendation for the current paper-support pass: keep Approach A as the
production configuration and report Approach C as feasible future work unless
Jason explicitly wants to spend implementation time on a depth-varying
candidate/support pass before submission.

## Rerun Instructions

Run from the repository root with the project virtualenv active or by invoking
`.venv/bin/python` directly.

Focused validation:

```bash
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
```

Run the notebook `6` hold-one-float-out validation from cached cycle models:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python research/underwater-acoustics/notebooks/run_notebook6_holdout_validation.py
```

Regenerate the cached product and chart files from the paired Python source:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python research/underwater-acoustics/notebooks/6-sound-speed-uncertainty-product.py
```

Sync source and notebook without executing:

```bash
.venv/bin/python -m jupytext --sync research/underwater-acoustics/notebooks/6-sound-speed-uncertainty-product.py
```

Execute and sync the notebook when embedded `.ipynb` outputs must match the
generated files:

```bash
MPLCONFIGDIR=/tmp/matplotlib-cache .venv/bin/python -m jupytext --execute --sync research/underwater-acoustics/notebooks/6-sound-speed-uncertainty-product.py
```

In the managed sandbox, Jupyter kernel socket creation can fail with
`PermissionError: [Errno 1] Operation not permitted`; execute outside the
sandbox when embedded outputs must be regenerated.

To force a full recomputation, delete the relevant ignored local cache files
under `research/underwater-acoustics/notebooks/data/` before rerunning. Delete
`sound_speed_uncertainty_spatial_variance.pkl` and
`sound_speed_uncertainty_product.pkl` to recompute the spatial variance bucket
and gridded product. Delete `pchip_cycle_models.pkl` only when the per-cycle
model bundle itself must be rebuilt from raw Argo data.

## Report-Back Points

For the downstream paper, the current confirmed map depth is `110` dbar,
reported as approximately `110 m` for figure naming. Queryable coverage is the
computed product grid, not the full rectangular plot extent; at the current
configuration some north/east plot cells are masked because no product rows
exist there after candidate/support filtering.

The support signal should be described as a model-free support diagnostic, not
as a fused reliability metric. It is not included in the variance formula.

Unvalidated or deferred claims:

- T-S covariance is deferred and treated as zero, not estimated.
- TEOS-10 formula uncertainty is acknowledged separately and not folded into
  `sigma_sound_speed_teos10`.
- EOS-80 propagation is not part of the current notebook `6` output.
- Per-cycle/per-float contribution exports remain to be built if the paper
  needs those tables rather than aggregate component buckets.
- The benchmark/scaling study remains to be run systematically.
