# Sound-Speed Uncertainty Implementation Plan

Date: 2026-07-02
Status: planning note for OCEANS 2026 paper-support implementation
Tracker: Kanboard `#159`, "OCEANS 2026 paper: technical deliverables (Coding Agent handoff)"

This note records the current code state and the target output shape for the
first implementation item: sound-speed uncertainty propagation. It is meant to
be recoverable by the Coding Agent before implementation resumes.

## Settled Scope

The implementation propagates variance under the independence simplification:

```text
var_c = (dc/dT)^2 var_T + (dc/dS)^2 var_S
```

The T-S covariance cross term is out of scope and deferred to future work:

```text
cov_TS = 0
```

The sound-speed equation nonlinearity is still carried by the partial
derivatives `dc/dT` and `dc/dS`; only the statistical covariance cross term is
dropped.

As of the current Kanboard card text, the sound-speed equation's intrinsic
formula uncertainty is not folded into the reported sigma. It is acknowledged
in the paper as an additional known uncertainty and left for future work.

`W` remains a separate model-free support signal. It is not fused with sigma or
any variance term into a combined reliability metric.

## Current Variance Inputs

### Per-cycle vertical model and sensor terms

The per-cycle model lives in `src/argo_interp/cycle/model/Model.py`.

`Model.build()` computes one scalar vertical model RMSE for temperature and one
for salinity using `calc_fold_error()`, then stores those values in
`CycleError`:

```text
CycleError.pressure
CycleError.temperature.model
CycleError.temperature.sensor
CycleError.salinity.model
CycleError.salinity.sensor
```

Default sensor accuracies are in
`src/argo_interp/cycle/config/SensorAccuracy.py`:

```text
pressure = 2.4
temperature = 0.002
salinity = 0.01
```

`Model.interp_error()` currently returns combined standard errors for
temperature and salinity at requested pressures. Internally,
`Model._measure_error()` combines three variance terms and square-roots them:

```text
sigma_T = sqrt(
    vertical_model_error_T^2
  + temperature_sensor_precision^2
  + (dT/dP * pressure_sensor_error)^2
)

sigma_S = sqrt(
    vertical_model_error_S^2
  + salinity_sensor_precision^2
  + (dS/dP * pressure_sensor_error)^2
)
```

This confirms pressure uncertainty is already propagated into T and S through
the vertical gradient. It also means the current public method collapses the
component buckets too early for the requested decomposition.

### Required componentized variance form

The implementation needs a componentized path that can preserve the following
cycle-level variance terms:

```text
var_T_sensor_precision
var_T_pressure_gradient
var_T_vertical_model

var_S_sensor_precision
var_S_pressure_gradient
var_S_vertical_model
```

where:

```text
var_T_pressure_gradient = (dT/dP)^2 * var_pressure_sensor
var_S_pressure_gradient = (dS/dP)^2 * var_pressure_sensor
```

The combined per-cycle variances are:

```text
var_T_cycle =
    var_T_sensor_precision
  + var_T_pressure_gradient
  + var_T_vertical_model

var_S_cycle =
    var_S_sensor_precision
  + var_S_pressure_gradient
  + var_S_vertical_model
```

### Weighted aggregate terms

The notebook support helper
`research/underwater-acoustics/notebooks/lib/prediction.py` provides
`weighted_profile_mean(values, weights)`, which computes a weighted mean with
finite-value support handling:

```text
sum(w_i x_i) / sum(w_i over finite x_i)
```

Notebook `5-uncertainty-model-build.py` currently computes:

```python
scaled_weight = total_weight / total_weight.sum()
...
var_temperature, var_salinity = weighted_cycle_prediction(interp_var, total_weight**2)
```

That is not the correct variance aggregation for a weighted mean, because
`weighted_cycle_prediction()` normalizes by `sum(w_i^2)` when passed
`total_weight**2`. The target aggregation must use squared normalized weights:

```text
alpha_i = w_i / sum(w_i over supported cycles)

var_T_aggregate = sum_i alpha_i^2 var_T_cycle_i + var_T_spatial
var_S_aggregate = sum_i alpha_i^2 var_S_cycle_i + var_S_spatial
```

The model-wide spatial interpolation errors, `var_T_spatial` and
`var_S_spatial`, are separate model buckets in T and S space. They are added
before sound-speed variance propagation. They are not the same thing as `W`.

The existing notebook computes validation residuals for T and S in the first
half of `5-uncertainty-model-build.py`, but it does not yet expose a reusable
`var_spatial` object for each query point/depth.

## Target Output Data Model

The paper-support pipeline should produce a table-like record per query point
and depth. For the 110 m decomposition figures this table can be filtered to
`depth_m == 110`.

Recommended columns:

```text
latitude
longitude
depth_m
pressure_dbar
timestamp_or_anchor_time

temperature
salinity

var_temperature_sensor_precision
var_temperature_pressure_gradient
var_temperature_vertical_model
var_temperature_spatial
var_temperature_aggregate
sigma_temperature_aggregate

var_salinity_sensor_precision
var_salinity_pressure_gradient
var_salinity_vertical_model
var_salinity_spatial
var_salinity_aggregate
sigma_salinity_aggregate

sound_speed_teos10

dc_teos10_dT
dc_teos10_dS
var_sound_speed_teos10
sigma_sound_speed_teos10

W_raw
W_display
candidate_cycle_count
effective_cycle_count
```

Recommended optional decomposition columns:

```text
var_sound_speed_teos10_from_temperature_sensor_precision
var_sound_speed_teos10_from_temperature_pressure_gradient
var_sound_speed_teos10_from_temperature_vertical_model
var_sound_speed_teos10_from_temperature_spatial
var_sound_speed_teos10_from_salinity_sensor_precision
var_sound_speed_teos10_from_salinity_pressure_gradient
var_sound_speed_teos10_from_salinity_vertical_model
var_sound_speed_teos10_from_salinity_spatial
```

These optional columns make the sensor-versus-model split straightforward:

```text
sensor bucket = sensor precision + pressure-gradient contribution
model bucket = vertical model error + spatial interpolation error
```

## Implementation Implications

1. Add a componentized interpolation-error path rather than relying only on
   `Model.interp_error()`, because `interp_error()` returns already-combined
   standard errors.
2. Add a correct weighted variance aggregation helper that uses
   squared normalized weights and finite-value support handling.
3. Add or compute the model-wide spatial variance bucket in T and S space before
   sound-speed propagation.
4. Add sound-speed point-estimate and derivative helpers for GSW / TEOS-10.
5. Keep outputs in variance space and derive sigma only as `sqrt(var)` for
   figures and human-facing summaries.

## Implementation Progress

2026-07-08 coding-agent pass:

- Added `Model.interp_error_variance()` and
  `CycleModels.interp_error_variance()` alongside the existing
  `interp_error()` sigma path.
- Added variance containers for the per-measure buckets:
  `sensor_precision`, `pressure_gradient`, and `vertical_model`.
- Added `weighted_profile_variance()` and `weighted_cycle_variance()` in the
  underwater-acoustics notebook support library. These helpers aggregate
  weighted-mean variance as `sum(alpha_i^2 var_i)` with finite-value support
  handling.
- Added `argo_interp.acoustics` helpers for GSW / TEOS-10 sound-speed point
  estimates, finite-difference partial derivatives with respect to temperature
  and practical salinity, and no-cross-term variance propagation.
- Added notebook `6-sound-speed-uncertainty-product` as the dedicated
  table-producing pipeline for the OCEANS 2026 uncertainty product, leaving
  notebook `5` as the deterministic model-build artifact.
- Updated notebook `6` and the acoustics helper to avoid the deprecated
  `seawater` package and use the modern GSW / TEOS-10 path only.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py -q
12 passed
```

2026-07-22 coding-agent continuation:

- Updated notebook `6-sound-speed-uncertainty-product` so the full-grid product
  build precomputes target-pressure cycle estimates and variance components
  once, then slices those arrays inside the lat/lon query loop. This replaced
  repeated per-grid-point model interpolation and variance-gradient evaluation.
- Changed the notebook flow so cached `pchip_cycle_models.pkl` runs do not load
  or unpickle the raw Argopy-backed Argo data cache. Raw data is loaded only
  when the cycle-model bundle must be rebuilt.
- Made `argo_interp.data.get_data` lazy at package import time so
  `argo_interp.data` and `argo_interp.data.data_filter` can be imported without
  initializing Argopy or touching its user cache.
- Updated `weighted_profile_mean()` to return `NaN` for zero-supported rows
  without emitting divide-by-zero runtime warnings.
- Regenerated notebook `6` from the paired Jupytext source without stale
  interrupted outputs.
- Completed the product build from cached inputs. Outputs written under
  `research/underwater-acoustics/notebooks/data/`:
  - `sound_speed_uncertainty_product.pkl` (`92,308 x 39`)
  - `sound_speed_uncertainty_product.csv` (`92,308 x 39`)
  - `sound_speed_uncertainty_product_110m.csv` (`23,077 x 39`)

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Product validation checks:

```text
depth counts: 23,077 rows each at 5, 35, 110, and 500 dbar
finite sigma_sound_speed_teos10 rows: 90,362 / 92,308
component-total max absolute variance delta: 1.42e-14
sigma_sound_speed_teos10 range: 0.7961984174 to 6.5140462934
W_display range: 0.0 to 0.9996508732
```

2026-07-22 chart continuation:

- Added the five immediate 110 m paper-support charts to notebook `6`:
  point estimate, propagated sigma, standalone `W_display`, point estimate
  with `W_display` as opacity, and sigma with `W_display` as opacity.
- Saved each chart as both PNG and SVG under
  `research/underwater-acoustics/notebooks/data/charts/`:
  - `sound_speed_teos10_110m`
  - `sigma_sound_speed_teos10_110m`
  - `w_display_110m`
  - `sound_speed_teos10_w_opacity_110m`
  - `sigma_sound_speed_teos10_w_opacity_110m`
- Updated notebook `6` to reuse the cached uncertainty product when present,
  so chart reruns do not recompute the full grid product unless the product
  pickle is deleted.
- Executed notebook `6` with Jupytext so the chart outputs are embedded in the
  `.ipynb`. The sandbox blocked Jupyter kernel socket creation, so execution
  required an approved outside-sandbox run.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Chart validation checks:

```text
all five PNG chart files exist and have nonblank image arrays
notebook contains embedded image/png output
no KeyboardInterrupt or Traceback remains in the executed notebook
```

2026-07-22 chart scaling adjustment:

- Updated both 110 m sigma charts to use the local `p01..p99`
  `sigma_sound_speed_teos10` range instead of anchoring the color scale at
  zero. For the current 110 m product, that scale is approximately
  `5.3588..6.1622 m/s`.
- Documented and softened the opacity transform for the two W-opacity charts.
  The support signal remains `W_display = 1 - exp(-W_raw / 40)`, but plotted
  opacity is now `alpha = 0.18 + 0.82 * sqrt(W_display)` for finite cells.
  This raises the current 110 m opacity quartiles from direct `W_display`
  values of `0.1466 / 0.7054 / 0.9223` to
  `0.4940 / 0.8687 / 0.9675`.
- Regenerated chart PNG/SVG exports and executed notebook `6` with Jupytext so
  the embedded `.ipynb` chart outputs match the saved files.
- Added a second legend beside each W-opacity chart's colorbar showing the
  plotted W-opacity ramp.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-22 land overlay adjustment:

- Added Cartopy `PlateCarree` map axes to all five 110 m chart exports and
  overlaid 50 m Natural Earth land and coastline features. Land renders above
  the raster so coast-adjacent signals can be read against the actual Bay of
  Bengal landmass.
- Cached the Natural Earth shapefiles under
  `research/underwater-acoustics/notebooks/data/cartopy/` for reproducible
  notebook reruns.
- Regenerated all chart PNG/SVG exports and executed notebook `6` with
  Jupytext so the embedded `.ipynb` outputs include the land overlay.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-22 support/opacity chart adjustment:

- Updated the standalone 110 m support-weight chart so missing raster cells are
  filled at `W_display = 0.0`, making no-support background read as the zero
  end of the support scale. Land remains the separate Natural Earth overlay.
- Tuned the W-opacity transform from
  `alpha = 0.18 + 0.82 * sqrt(W_display)` to
  `alpha = 0.15 + 0.85 * W_display ** 0.6`. For the current 110 m product,
  plotted opacity quartiles are now `0.4186 / 0.8394 / 0.9597`.
- Regenerated all chart PNG/SVG exports and executed notebook `6` with
  Jupytext so the embedded `.ipynb` outputs match the saved files.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-22 support extent adjustment:

- Reindexed all 110 m figure matrices onto the configured full Bay chart grid
  (`6..23 N`, `80..99 E`) before plotting. The cached 110 m product contains
  computed rows only through about `21.8 N` and `97.3 E`; reindexing makes the
  chart extent match the map extent without inventing science-field values.
- The standalone support-weight chart still fills missing matrix cells as
  `W_display = 0.0`, so no-support background now covers the full map area.
  Non-support science fields remain masked where no product value exists.
- Regenerated all chart PNG/SVG exports and executed notebook `6` with
  Jupytext so the embedded `.ipynb` outputs match the saved files.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-22 temporal/seasonal weighting rerun:

- Switched notebook `6` from distance-only weighting to distance + absolute
  time + wrapped seasonal weighting by setting `use_time_weight = True` and
  `use_season_weight = True`.
- Added JSON metadata guards for the spatial-variance and uncertainty-product
  caches so stale spatial-only pickles are not reused when the weighting
  configuration changes.
- Recomputed the spatial validation variance bucket and full uncertainty
  product under the temporal/seasonal configuration, then regenerated the CSV,
  PNG/SVG chart exports, and executed `.ipynb` outputs.
- Current product metadata confirms `use_time_weight = True` and
  `use_season_weight = True`. The refreshed product has `92,308` rows, with
  `23,077` rows at 110 m and `22,636` finite 110 m sigma values.
- The 110 m sigma color range is now approximately `4.1629..5.3442 m/s`
  (`p01..p99`). The 110 m `W_display` quartiles are
  `0.0125 / 0.0878 / 0.1860`, reflecting the stricter combined temporal and
  seasonal support.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-22 heatmap display interpolation adjustment:

- Switched the map heatmap raster display interpolation from nearest-neighbor
  to bilinear for both scalar charts and W-opacity charts. This smooths visible
  cell blockiness from the 0.1-degree plotting grid without changing the cached
  uncertainty product.
- The north/east support still decays to near zero under the temporal/seasonal
  configuration. The remaining far-northeast opacity-chart boundary is a
  product coverage boundary, not a smooth model field: there are no computed
  product rows beyond roughly `21.8 N` and `97.3 E`.
- Regenerated all chart PNG/SVG exports and executed notebook `6` with
  Jupytext so the embedded `.ipynb` outputs match the saved files.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-22 chart title and edge-structure note:

- Added the analysis date from `anchor_time` to all five 110 m chart titles.
  The current chart title suffix is `Analysis date: 2015-07-01`.
- Confirmed that remaining hard edge structure is not produced by the Gaussian
  kernel itself. The notebook first applies a hard spatial candidate prefilter
  through `build_candidate_query(..., dist_rad=dist_rad)`, then applies the
  Gaussian distance/time/season weights to that candidate set. That prefilter
  can create coverage boundaries even though the kernel weights are smooth
  inside the selected set.
- Regenerated all chart PNG/SVG exports and executed notebook `6` with
  Jupytext so the embedded `.ipynb` outputs match the saved files.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 6-sigma candidate-window rerun:

- Widened the hard spatial candidate prefilter from `3 sigma` to `6 sigma`
  by setting `candidate_radius_sigma = 6.0`. The distance kernel itself remains
  unchanged at `distance_kernel_sigma_deg = 1/3`, so the prefilter radius is
  now `dist_rad = 2.0` degrees.
- Recomputed the spatial validation variance cache and full uncertainty
  product with temporal and seasonal weighting still enabled, then regenerated
  the CSV, PNG/SVG chart exports, and executed `.ipynb` outputs.
- Runtime signal from the direct source run: spatial validation took about
  `12:00`; the gridded product build took about `1:45`. Notebook execution
  after cache refresh completed quickly because it reused the rebuilt caches.
- Current product metadata confirms `candidate_radius_sigma = 6.0`,
  `dist_rad = 2.0`, and `distance_kernel_sigma_deg = 0.3333333333333333`.
  The refreshed product has `109,200` rows, with `27,300` rows at 110 m and
  `26,825` finite 110 m sigma values.
- The 110 m sigma color range is approximately `4.1160..5.3171 m/s`
  (`p01..p99`). The 110 m `W_display` quartiles are
  `0.0004 / 0.0570 / 0.1644`.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 candidate-window revert to 3-sigma:

- Reverted `candidate_radius_sigma` from `6.0` back to `3.0`, returning the
  hard spatial candidate prefilter to `dist_rad = 1.0` degree while preserving
  the Gaussian distance kernel sigma at `1/3` degree.
- Recomputed the spatial validation variance cache and full uncertainty
  product with temporal and seasonal weighting still enabled, then regenerated
  the CSV, PNG/SVG chart exports, and executed `.ipynb` outputs.
- Runtime signal from the direct source run: spatial validation took about
  `4:15`; the gridded product build took about `1:14`. This restores the
  lower-cost configuration after the 6-sigma test showed remaining edge
  blockiness was not worth the extra processing time.
- Current product metadata confirms `candidate_radius_sigma = 3.0`,
  `dist_rad = 1.0`, `use_time_weight = True`, and
  `use_season_weight = True`. The refreshed product has `92,308` rows, with
  `23,077` rows at 110 m and `22,636` finite 110 m sigma values.
- The 110 m sigma color range is approximately `4.1629..5.3442 m/s`
  (`p01..p99`). The 110 m `W_display` quartiles are
  `0.0125 / 0.0878 / 0.1860`.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support-chart background revert:

- Removed the `fill_missing=0.0` override from the standalone 110 m support
  weight chart. Missing product cells now render as masked/white again, which
  keeps this chart visually consistent with the rest of the exported set.
- Left the 3-sigma candidate radius, temporal/seasonal weighting, bilinear
  display interpolation, opacity scales, and land overlays unchanged.
- Regenerated the chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 sound-speed opacity colormap adjustment:

- Added a custom hue-focused colormap for only the 110 m sound-speed opacity
  chart: blue -> teal -> green -> ochre -> orange -> red.
- Left the regular sound-speed chart on `turbo`; left the sigma charts,
  support chart, 3-sigma candidate radius, temporal/seasonal weighting, opacity
  scale, bilinear interpolation, and land overlays unchanged.
- Regenerated the chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 sound-speed opacity brightness adjustment:

- Brightened the custom sound-speed opacity colormap while preserving the same
  hue progression and numeric sound-speed limits. The updated ramp is
  `#6682ff -> #24c8df -> #4fe989 -> #e8ea4f -> #ffb03d -> #ff6262`.
- Left the regular sound-speed chart, sigma charts, support chart, opacity
  scale, 3-sigma candidate radius, temporal/seasonal weighting, interpolation,
  and land overlays unchanged.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 sound-speed opacity saturation adjustment:

- Increased saturation of the custom sound-speed opacity colormap while keeping
  the brightness/value level high. The updated ramp is
  `#3056ff -> #00c4df -> #19e967 -> #e7ea19 -> #ff9700 -> #ff2b2b`.
- Left the regular sound-speed chart, sigma charts, support chart, opacity
  scale, 3-sigma candidate radius, temporal/seasonal weighting, interpolation,
  and land overlays unchanged.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 opacity fade easing:

- Raised the shared opacity floor for W-opacity charts from `0.15` to `0.25`,
  changing finite-cell opacity from `0.15 + 0.85 * W_display ** 0.6` to
  `0.25 + 0.75 * W_display ** 0.6`.
- Left `opacity_exponent = 0.6`, the 3-sigma candidate radius,
  temporal/seasonal weighting, colormaps, interpolation, and land overlays
  unchanged.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 opacity curve correction:

- Corrected the W-opacity tuning to change the curve rather than raising the
  floor. The shared transform is now `alpha = W_display ** 0.25`, with
  `opacity_floor = 0.0`.
- Updated the standalone 110 m support-weight chart to stay fully opaque while
  using an opaque `viridis`-derived colormap composited against the map
  background with the same `W_display ** 0.25` curve. Its color gradient now
  matches the opacity bleedoff without adding an alpha layer or a second
  opacity legend.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support-chart alpha removal:

- Made the 110 m support-weight chart fully opaque in both PNG and SVG output.
  The support-specific colormap is now RGB-only, with missing cells set to
  opaque white and the support-chart gridlines rendered without opacity.
- Preserved the support-color bleedoff by compositing `viridis(W_display)`
  against the map background using the same `W_display ** 0.25` curve used as
  true alpha on the sound-speed and sigma opacity charts.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Support export opacity checks:

```text
w_display_110m.png alpha_minmax 255 255; transparent_pixels 0
w_display_110m.svg opacity=0, fill-opacity=0, stroke-opacity=0
```

2026-07-23 support-chart colormap adjustment:

- Replaced the support-weight chart's composited-viridis ramp with a dedicated
  fully opaque saturation-style support colormap. Finite `W_display = 0` now
  renders near black instead of white, while increasing support moves into a
  more saturated teal/green ramp.
- Kept the same `W_display ** 0.25` shaping used by the opacity charts, but
  applied it to the support colormap rather than to an alpha channel.
- Missing product cells remain opaque white so they stay visually distinct from
  finite zero-support cells.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Support export opacity checks:

```text
w_display_110m.png alpha_minmax 255 255; transparent_pixels 0
w_display_110m.svg opacity=0, fill-opacity=0, stroke-opacity=0
```

2026-07-23 support-chart hue/saturation refinement:

- Refined the fully opaque support-weight colormap so the transition into
  finite `W_display = 0` is continuous rather than a forced black endpoint.
  Low support now dips smoothly through dark/desaturated values.
- Added a modest hue gradient across the support ramp while keeping the chart
  mostly saturation-driven: low-to-mid support leans blue-cyan and higher
  support moves toward saturated green.
- Kept the `W_display ** 0.25` curve as the shared shaping function for the
  support colormap and the opacity charts. The support chart still uses no
  alpha channel.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Support export opacity checks:

```text
w_display_110m.png alpha_minmax 255 255; transparent_pixels 0
w_display_110m.svg opacity=0, fill-opacity=0, stroke-opacity=0
```

2026-07-23 support-chart red-yellow-green refinement:

- Changed the fully opaque support-weight colormap hue path from blue-cyan to
  green into a red/brown -> yellow/olive -> green ramp.
- Removed the forced black zero endpoint. Finite `W_display = 0` now starts as
  a dark muted red/brown, and near-zero values transition continuously through
  the same ramp.
- Kept `W_display ** 0.25` as the shared support shaping signal, but damped
  the low-end value/saturation response with a smoothstep curve so the color
  transition away from zero is less abrupt.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Support export opacity checks:

```text
w_display_110m.png alpha_minmax 255 255; transparent_pixels 0
w_display_110m.svg opacity=0, fill-opacity=0, stroke-opacity=0
```

2026-07-23 support-chart region colormap:

- Scrapped the red/yellow/green support colormap and replaced it with a
  continuous but region-readable ramp: low support is dark blue/purple, mid
  support is cyan/teal, and high support is saturated green.
- Kept the support chart fully opaque and kept `W_display ** 0.25` as the
  lookup shaping curve, matching the opacity chart's support response without
  adding alpha to the support chart.
- Missing product cells remain opaque white so they stay distinct from finite
  low-support regions.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Support export opacity checks:

```text
w_display_110m.png alpha_minmax 255 255; transparent_pixels 0
w_display_110m.svg opacity=0, fill-opacity=0, stroke-opacity=0
```

2026-07-23 support-chart distinct-region and zero-transparency update:

- Rebuilt the standalone 110 m support-weight chart around a more distinctive
  continuous support ramp: low support is purple/blue, mid support is orange,
  and high support is green.
- Added a support-chart-specific RGBA renderer so display-zero cells are
  transparent while finite nonzero cells are fully opaque. To avoid numerical
  dust reading as a dark zero band, the chart treats
  `W_display <= 0.001` as display-zero for this visualization only.
- Missing product cells remain opaque white, distinct from transparent
  display-zero support cells.
- Left the sound-speed and sigma W-opacity charts on their existing continuous
  `W_display ** 0.25` alpha scale.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support-chart zero cutoff correction:

- Removed the support-chart-only near-zero transparency cutoff. Only exact
  finite `W_display == 0` now renders transparent; finite nonzero support
  values render through the continuous colormap and remain fully opaque.
- This fixes the artificial white-to-dark-blue jump that was introduced by
  treating `W_display <= 0.001` as display-zero.
- Missing product cells still render opaque white, and the sound-speed/sigma
  W-opacity charts remain unchanged.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support-chart Jenks alignment:

- Re-aligned the standalone 110 m support-weight chart to the 3-class Jenks
  natural breaks for `W_display`: `0.0..0.126986598` low support,
  `0.126986598..0.423339948` mid support, and
  `0.423339948..1.0` high support.
- Replaced the previous continuous support ramp with a discrete
  `BoundaryNorm`/`ListedColormap` class map: blue for low support, orange for
  mid support, and green for high support. The colorbar now shows the Jenks
  break values directly.
- Kept exact finite `W_display == 0` transparent on the support layer, with
  all finite nonzero values fully opaque. Missing product cells remain opaque
  white.
- Switched only the support chart layer to nearest-neighbor interpolation so
  transparent zero cells do not bilinearly blend with neighboring colors and
  create cream-colored halos. Other scalar and W-opacity charts remain on
  bilinear display interpolation.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Jenks class counts at 110 m:

```text
low  0.0..0.126986598      14,251 cells  61.75%
mid  0.126986598..0.423339948 7,792 cells 33.77%
high 0.423339948..1.0       1,034 cells   4.48%
exact zeros                    675 cells   2.92%
```

2026-07-23 support-chart Jenks-anchored gradient:

- Replaced the discrete Jenks class colors with a continuous support-weight
  gradient anchored at the Jenks cluster means rather than at the boundaries:
  blue at the low-support mean (`0.0400414934`), orange at the mid-support
  mean (`0.214045957`), and green at the high-support mean (`0.633575923`).
- Kept the Jenks natural breaks (`0.0`, `0.126986598`, `0.423339948`, `1.0`)
  as colorbar ticks so the low/mid/high regions remain readable while the map
  uses smooth color transitions.
- Kept exact finite `W_display == 0` transparent on the support layer, with
  all finite nonzero values fully opaque. Missing product cells remain opaque
  white.
- Left the support chart layer on nearest-neighbor rendering to avoid
  reintroducing cream-colored interpolation halos around transparent zero
  cells. Other scalar and W-opacity charts remain on bilinear display
  interpolation.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support-chart colorbar cluster labels:

- Added `Low`, `Mid`, and `High` labels to the standalone 110 m support-weight
  colorbar at the Jenks cluster mean values: `0.0400414934`, `0.214045957`,
  and `0.633575923`.
- Rotated the cluster labels 90 degrees and placed them to the right of the
  colorbar. Moved numeric break ticks to the left side and placed `W display`
  as the colorbar title to avoid overlap.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support-chart interval-center labels:

- Moved the support-weight color anchors and `Low`/`Mid`/`High` colorbar
  labels from Jenks cluster means to the centers of the Jenks intervals:
  `0.063493299`, `0.275163273`, and `0.711669974`.
- Kept the Jenks natural breaks (`0.0`, `0.126986598`, `0.423339948`, `1.0`)
  as numeric colorbar ticks.
- Gave the support colorbar a separate padded axis so the map no longer crowds
  the numeric ticks or the right-side cluster labels.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 sound-speed opacity Jenks alpha bins:

- Changed only the 110 m sound-speed W-opacity chart to use Jenks-binned
  support opacity instead of the continuous `W_display ** 0.25` alpha curve.
- Used the current 3-class Jenks support breaks:
  `0.0..0.126986598` low, `0.126986598..0.423339948` mid, and
  `0.423339948..1.0` high.
- Mapped those classes to discrete plotted opacity values: low support
  `alpha = 0.25` (75% transparent), mid support `alpha = 0.50`, and high
  support `alpha = 1.00` (no transparency). Missing/non-finite support remains
  transparent.
- Updated the sound-speed opacity legend to show the same discrete alpha
  steps. Left the sigma W-opacity chart on the existing continuous
  `W_display ** 0.25` alpha scale.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Sound-speed opacity class counts at 110 m:

```text
alpha 0.25  14,251 cells  61.75%
alpha 0.50   7,792 cells  33.77%
alpha 1.00   1,034 cells   4.48%
```

2026-07-23 sound-speed W-saturation chart:

- Replaced support alpha as the W-display differentiator on the 110 m
  sound-speed W chart with support-controlled saturation. The chart title is
  now `Bay of Bengal TEOS-10 Sound Speed at 110 m with W Saturation`.
- Kept the same 3-class Jenks support breaks:
  `0.0..0.126986598` low, `0.126986598..0.423339948` mid, and
  `0.423339948..1.0` high.
- Mapped those classes to discrete saturation multipliers: low support
  `0.25`, mid support `0.50`, and high support `1.00`. All finite cells on
  the sound-speed W chart are now fully opaque; missing/non-finite support
  remains transparent.
- Updated the W-display side scale on the sound-speed W chart to match the
  support-weight chart labeling: numeric Jenks break ticks plus rotated
  `Low`/`Mid`/`High` labels at the interval centers
  `0.063493299`, `0.275163273`, and `0.711669974`.
- Increased spacing between the sound-speed colorbar and W-display saturation
  scale, and moved the sound-speed colorbar label to the left side to avoid
  label overlap.
- Left the sigma W-opacity chart on the existing continuous
  `W_display ** 0.25` alpha scale.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

Sound-speed saturation class counts at 110 m:

```text
saturation 0.25  14,251 cells  61.75%
saturation 0.50   7,792 cells  33.77%
saturation 1.00   1,034 cells   4.48%
```

2026-07-23 sound-speed W-contour chart:

- Removed support-controlled saturation from the 110 m sound-speed W chart.
- Replaced W-display demarcation with contour lines at the two internal Jenks
  support breaks: `W=0.126986598` and `W=0.423339948`.
- Dashed contour marks the low/mid support boundary; solid contour marks the
  mid/high support boundary. Both contours use a dark line with a white halo and
  a compact lower-left legend.
- Left the sound-speed color scale fully opaque and unchanged aside from the W
  contour overlay. The old export stem remains
  `sound_speed_teos10_w_opacity_110m` for continuity, but the chart title now
  reads `Bay of Bengal TEOS-10 Sound Speed at 110 m with W Contours`.
- Left the sigma W-opacity chart on the existing continuous
  `W_display ** 0.25` alpha scale, and left the standalone support chart on the
  Jenks-anchored support gradient.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 inline W contour labels:

- Added inline contour labels to the 110 m sound-speed W-contour chart so the
  support break value is printed directly on the contour path as `W=0.127` or
  `W=0.423`.
- Kept the separate line styles: dashed for the low/mid support boundary and
  solid for the mid/high support boundary.
- Applied the same white halo treatment to the inline labels so they remain
  readable over the fully opaque sound-speed color field.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 raw support distribution plot:

- Added a sixth chart export, `w_raw_distribution_110m`, showing the 110 m
  distribution of finite `W_raw` support scores.
- The histogram uses 80 bins and a log-scaled count axis so the low-score mass
  and long high-support tail are visible in the same panel.
- Added vertical boundary markers for the current display-based support contour
  breaks converted back to raw support units:
  `W_display=0.126986598 -> W_raw=5.43` and
  `W_display=0.423339948 -> W_raw=22.02`.
- Kept the dashed/solid styling consistent with the contour map: dashed for
  low/mid and solid for mid/high.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 raw support distribution quartile markers:

- Updated `w_raw_distribution_110m` to replace the converted display-boundary
  reference lines with `W_raw` quartile reference lines.
- The plotted quartiles for finite 110 m grid cells are:
  `Q1=0.50332673`, `median=3.67366654`, and `Q3=8.23108506`.
- Kept the histogram on a log-scaled count axis so the low-support mass and
  long high-support tail remain visible.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 raw support distribution visual quartiles:

- Updated `w_raw_distribution_110m` to show visual-weighted quartiles instead
  of true `W_raw` quartiles.
- Visual quartiles are computed over the same 80-bin histogram shown in the
  chart using `log(count + 1)` as each bin's visual weight, with linear
  interpolation inside the selected bin.
- The plotted visual quartiles for the finite 110 m `W_raw` histogram are:
  `Q1=11.72100102`, `median=30.82085989`, and `Q3=57.22189630`.
- The legend labels these as `Visual Q1`, `Visual median`, and `Visual Q3` to
  distinguish them from ordinary data quartiles.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 sound-speed raw visual-quartile contours:

- Updated the 110 m sound-speed contour chart to use `W_raw` visual quartiles
  as contour levels instead of the earlier `W_display` Jenks boundaries.
- Added `W_raw` to the 110 m figure-ready matrix set so the map contours the
  raw support surface directly.
- Reused the same `log(count + 1)` 80-bin visual-quartile calculation used by
  `w_raw_distribution_110m`.
- The plotted contour levels are `W_raw=11.72100102`,
  `W_raw=30.82085989`, and `W_raw=57.22189630`, labeled as `Visual Q1`,
  `Visual median`, and `Visual Q3`.
- Kept distinct line styles on the map: dashed for Visual Q1, solid for Visual
  median, and dash-dot for Visual Q3. Inline labels now print `W raw=...`.
- Fixed a plotting helper bug where the inline label list shadowed the
  user-supplied contour-label list after the first contour.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 sound-speed raw quartile contours:

- Updated the 110 m sound-speed contour chart to use true finite `W_raw`
  quartiles instead of visual-weighted raw-support quartiles.
- The plotted contour levels are `Q1=0.50332673`,
  `median=3.67366654`, and `Q3=8.23108506`.
- Kept the line styles from the previous contour version: dashed for Q1, solid
  for median, and dash-dot for Q3. Inline labels print `W raw=...`.
- Moved the sound-speed contour legend to the upper-left corner.
- Left `w_raw_distribution_110m` on visual-weighted quartile markers and left
  the standalone support chart and sigma W-opacity chart unchanged.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 square-root raw support distribution:

- Added a separate chart export, `sqrt_w_raw_distribution_110m`, showing the
  110 m distribution of `sqrt(W_raw)`.
- Left the existing `w_raw_distribution_110m` chart unchanged so the raw and
  square-root transformed distributions can be compared side by side.
- Generalized the support-distribution plotting helper to accept an optional
  x-value transform, x-axis label, and value label.
- The square-root chart keeps the same 80-bin histogram and log-count y-axis.
  Its visual-weighted quartile markers are
  `sqrt(W_raw)=1.75380686`, `sqrt(W_raw)=3.49054698`, and
  `sqrt(W_raw)=6.14848857`.
- For reference, the true finite `sqrt(W_raw)` quartiles are
  `0.70945523`, `1.91668113`, and `2.86898676`.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 exploratory raw support contours at 5 and 20:

- Updated the 110 m sound-speed contour chart to use two arbitrary exploratory
  `W_raw` contour levels: `5.0` and `20.0`.
- Kept the top-left legend, inline `W raw=...` labels, and distinct line
  styles: dashed for `W_raw=5.0` and solid for `W_raw=20.0`.
- Left the raw and square-root raw distribution charts unchanged, and left the
  standalone support chart and sigma W-opacity chart unchanged.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support chart raw-threshold re-anchoring:

- Updated the standalone `w_display_110m` support chart to use the same raw
  support dividing choices as the sound-speed contour map: `W_raw=5.0` and
  `W_raw=20.0`.
- Kept the chart plotted in `W_display`, so the raw thresholds are converted
  through `W_display = 1 - exp(-W_raw / 40)`.
- Resulting display-space break ticks are `0.1175030974` and `0.3934693403`.
- Recentered the color-anchor and cluster-label positions at display-space
  interval midpoints: Low `0.0587515487`, Mid `0.2554862189`, and High
  `0.6967346701`.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 raw-valued standalone support chart:

- Switched the standalone support chart from display-space `W_display` values
  to raw `W_raw` values.
- Renamed the chart export from `w_display_110m` to `w_raw_110m` and updated
  the chart title/colorbar label to raw support terminology.
- Kept the dividing choices at raw `W=5.0` and `W=20.0`; the colorbar now
  ticks raw values directly at `0.0`, `5.0`, `20.0`, and the observed raw
  maximum (`114.4` in the regenerated export).
- Recentered the color-anchor and cluster-label positions in raw space: Low at
  `2.5`, Mid at `12.5`, and High halfway between `20.0` and the observed raw
  maximum.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 log-scaled raw support colorbar:

- Changed the standalone `w_raw_110m` support chart to use `LogNorm` while
  keeping the chart values and colorbar tick labels in raw `W` units.
- Kept exact zero support transparent. Since zero cannot be represented on a
  log scale, it is not drawn as a colorbar tick.
- Found the smallest positive raw support value is effectively zero
  (`5.86462e-25`), which collapsed the useful `5`, `20`, and high-support
  range into the top of the colorbar when used as the literal log minimum.
- Set a practical raw log floor of `W=1.0`; positive support below `1.0`
  renders with the low under-range color, while exact zero remains transparent.
- The regenerated colorbar uses raw ticks at `1`, `5`, `20`, and the observed
  raw maximum (`114.4` in the export), with Low/Mid/High labels still centered
  at raw values `2.5`, `12.5`, and halfway between `20.0` and the max.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 linear raw support render with log-spaced bar:

- Reverted the standalone `w_raw_110m` map rendering to the prior linear raw
  `W` color normalization so the spatial image again matches the pre-log map
  appearance.
- Kept the colorbar axis log-spaced with raw tick labels at `1`, `5`, `20`,
  and the observed raw maximum (`114.4` in the export).
- Implemented the support colorbar as a custom log-y-axis bar so tick spacing
  can be logarithmic while the map colors remain linear raw `W`.
- Kept exact zero support transparent and retained the `W=1.0` lower colorbar
  floor because the finite positive raw minimum is effectively zero.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 visually centered support colorbar labels:

- Moved the standalone `w_raw_110m` Low/Mid/High side labels to the visual
  centers of their log-spaced colorbar regions instead of reusing the map color
  anchor points.
- Kept map color anchors at the linear raw midpoints used for rendering:
  `2.5`, `12.5`, and halfway between `20.0` and the observed raw maximum.
- Set label positions to geometric midpoints on the log-spaced bar:
  Low `sqrt(1.0 * 5.0)`, Mid `sqrt(5.0 * 20.0)`, and High
  `sqrt(20.0 * W_raw_max)`.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 drop support distribution charts and threshold rationale:

- Removed the raw `W` and square-root raw `W` distribution chart exports from
  notebook `6`; `chart_exports` now contains the five map/sigma/support figures
  only.
- Deleted the stale generated distribution PNG/SVG artifacts from
  `research/underwater-acoustics/notebooks/data/charts`.
- Removed the now-unused distribution plotting helper and visual-weighted
  histogram quantile helper from the paired Python notebook source.
- Updated the chart-section markdown to describe the current five-export set.
- Rationale for retaining raw thresholds `5.0` and `20.0`:
  `W_raw` is the unnormalized sum of finite-cycle joint kernel weights, so it
  is a kernel-mass measure rather than a normalized confidence score. Because
  each joint kernel weight is at most `1.0`, `W_raw=5` and `W_raw=20` can be
  read as roughly five and twenty perfectly matched profile-equivalents of
  support mass.
- At 110 m, the empirical split is: zero support `1.91%`, low positive support
  `0<W<5` `57.19%`, mid support `5<=W<20` `35.94%`, and high support
  `W>=20` `4.95%`.
- The bands also map to meaningful effective-count changes: median
  `N_eff=7.07` below `5`, `34.4` from `5` to `20`, and `115` above `20`.
  That makes the bands useful as support-regime markers even though the exact
  thresholds remain interpretive rather than a formal statistical test.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support hues aligned to log colorbar transform:

- Updated the standalone `w_raw_110m` support chart so the map hue assignment
  uses the same log-spaced raw `W` transform as the colorbar.
- Raw `W` remains the plotted value and the colorbar still labels raw ticks at
  `1`, `5`, `20`, and the observed raw maximum.
- Exact zero support remains transparent; positive values below the `W=1.0`
  log floor render with the under-range low-support color.
- Color anchors still represent raw support-region midpoints (`2.5`, `12.5`,
  and halfway between `20.0` and the max), but their colormap positions are now
  calculated through `LogNorm` instead of `value / W_raw_max`.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 support chart raw contour overlay:

- Added the same raw support contours used on the sound-speed contour chart to
  the standalone `w_raw_110m` support-weight chart.
- Factored contour drawing into `add_support_contours(...)` so the sound-speed
  and support charts share the same `W_raw=5.0`/`20.0` levels, line styles,
  white stroke halo, inline labels, and legend formatting.
- The support chart now renders dashed `W raw=5.00` and solid `W raw=20.00`
  contours with the legend in the upper-left corner.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-23 contour label cleanup:

- Removed inline value text from the raw support contour lines on both the
  sound-speed contour chart and the standalone support-weight chart.
 - Rewrote the shared contour legend entries from redundant value labels to
  region-boundary labels: `Low/Mid boundary (W=5)` and
  `Mid/High boundary (W=20)`.
- Kept the shared dashed/solid line styles, white halo, and upper-left legend.
- Regenerated chart exports and executed `.ipynb` outputs with Jupytext.

Focused validation run:

```text
.venv/bin/python -m pytest tests/test_acoustics.py tests/test_model_and_error.py tests/test_underwater_acoustics_prediction_helpers.py tests/test_validation_and_data.py -q
15 passed
```

2026-07-25 handoff closeout pass:

- Renamed the sound-speed support-contour chart export from the stale
  `sound_speed_teos10_w_opacity_110m` stem to
  `sound_speed_teos10_w_contours_110m`. The chart itself already used raw
  `W_raw=5` and `W_raw=20` contours rather than W opacity; the export name now
  matches the visual grammar.
- Added `sound_speed_uncertainty_depth_summary.csv` as a small depth-resolved
  report artifact derived from the full product. It reports one row per target
  pressure with row counts, finite sigma counts, sigma quantiles, support
  medians, and effective/candidate cycle-count medians.
- Added
  `research/underwater-acoustics/notes/sound-speed-uncertainty-handoff-report.md`
  as the concise Coding Agent report-back against Kanboard `#159`, including
  completed, partial, and deferred items; rerun instructions; benchmark plan;
  and Approach A/C feasibility notes.
- Executed notebook `6` through Jupytext outside the sandbox after local kernel
  socket creation was blocked by sandbox permissions. Embedded `.ipynb` outputs
  now reference `sound_speed_teos10_w_contours_110m`.

2026-07-25 chart finalization:

- Applied the custom sound-speed contour colormap to the regular
  `sound_speed_teos10_110m` chart, so the plain sound-speed map and the
  sound-speed contour map use the same color grammar.
- Replaced the sigma W-opacity chart with a sigma raw-W contour chart using
  the same `W_raw=5` and `W_raw=20` contour levels, line styles, legend labels,
  and support matrix as the sound-speed contour chart.
- Renamed the sigma support-overlay export from
  `sigma_sound_speed_teos10_w_opacity_110m` to
  `sigma_sound_speed_teos10_w_contours_110m`.
- Removed the unused support-opacity plotting helper from notebook `6`.

2026-07-25 benchmark output pass:

- Added a cached-input product benchmark section to notebook `6`. The benchmark
  measures the path used for figure iteration: cached cycle models plus cached
  spatial variance, then query-product row construction.
- Wrote benchmark outputs under
  `research/underwater-acoustics/notebooks/data/`:
  - `sound_speed_uncertainty_benchmark.csv`
  - `sound_speed_uncertainty_benchmark_metadata.json`
- The benchmark varies grid step and target-pressure count across six cases:
  `grid_1p0_depth1`, `grid_1p0_depth4`, `grid_0p5_depth1`,
  `grid_0p5_depth4`, `grid_0p25_depth4`, and `grid_0p1_depth4`.
- The production benchmark case, `grid_0p1_depth4`, produced `92,308` rows,
  `90,362` finite sigma rows, `173.80` seconds of measured row-construction
  wall time, `48.10` seconds of one-time cycle-target precompute time, and
  `151.999` MB of peak traced Python memory. These benchmark timings were
  measured on Jason's `galatea` system.
- The benchmark intentionally does not measure raw Argo download, per-cycle
  model rebuild, or spatial-variance recomputation.

2026-07-25 notebook 6 full holdout validation pass:

- Added `run_notebook6_holdout_validation.py` to run a full
  hold-one-float-out validation under the final notebook `6` configuration from
  cached PCHIP cycle models.
- The validation predicts each held-out cycle at `5`, `35`, `110`, and `500`
  dbar from other platforms only, using the final `dist_rad = 1.0` hard spatial
  prefilter and final distance/time/season Gaussian weights.
- Wrote generated outputs under
  `research/underwater-acoustics/notebooks/data/`:
  - `sound_speed_uncertainty_holdout_validation.csv`
  - `sound_speed_uncertainty_holdout_validation_summary.csv`
  - `sound_speed_uncertainty_holdout_validation_metadata.json`
- The run used `20,986` cached cycle models, skipped `4` cycles with no
  non-platform candidate support, wrote `83,928` detail rows, and completed in
  `70.42` seconds from cache on Jason's `galatea` system.
- Summary TEOS-10 sound-speed RMSE by pressure: `1.6216 m/s` at `5` dbar,
  `1.7362 m/s` at `35` dbar, `4.6891 m/s` at `110` dbar, and `0.7543 m/s` at
  `500` dbar.

2026-07-25 support-contour threshold rerender:

- Moved the finalized raw-support contour thresholds from `W_raw=5` and
  `W_raw=20` to `W_raw=6` and `W_raw=30`.
- Updated the standalone raw-support chart colorbar breaks and legend labels
  to match the new thresholds.
- Re-anchored the Low, Mid, and High support colors at the geometric midpoint
  of each log-scaled raw-support range.
- Re-executed notebook `6` with Jupytext outside the sandbox and regenerated
  embedded `.ipynb` outputs plus chart PNG/SVG exports.

2026-07-25 matched replication-grid holdout validation:

- Reworked `run_notebook6_holdout_validation.py` to run notebook `6` and a
  flat Jana-style predictor through one matched hold-one-float-out harness.
- The rerun uses a `5` to `500` m inclusive depth grid at `1` m spacing
  (`496` levels). Per held-out cycle, `depth_m` is converted to `pressure_dbar`
  with `gsw.p_from_z(-depth_m, cycle_latitude)` before PCHIP interpolation.
- Both predictors use the same held-out cycles and the same shared 2 degree by
  2 degree spatial candidate window. Cycles with fewer than `30` non-platform
  candidates are skipped for both predictors.
- Added per-row predicted sigma columns for temperature, salinity, and TEOS-10
  sound speed, with `no_spatial` and `with_spatial` variants, plus pooled and
  by-depth coverage summaries.
- Wrote generated outputs under `research/underwater-acoustics/notebooks/data/`:
  - `sound_speed_uncertainty_holdout_validation_replication_grid_detail.csv`
  - `sound_speed_uncertainty_holdout_validation_replication_grid_cycle_summary.csv`
  - `sound_speed_uncertainty_holdout_validation_replication_grid_predictor_summary.csv`
  - `sound_speed_uncertainty_holdout_validation_replication_grid_depth_summary.csv`
  - `sound_speed_uncertainty_holdout_validation_replication_grid_sigma_coverage.csv`
  - `sound_speed_uncertainty_holdout_validation_replication_grid_spatial_variance.csv`
  - `sound_speed_uncertainty_holdout_validation_replication_grid_metadata.json`
- The run evaluated `20,779` held-out cycles, skipped `207` cycles for low
  support, wrote `10,306,384` detail rows, and completed in `1,925.60` seconds
  (`32:05.60`) from cached PCHIP cycle models on Jason's `galatea` system.
- Notebook `6` won the matched per-cycle p75 RMSE comparison over the flat
  Jana-style predictor for temperature (`1.0500` vs `1.3419 deg C`), salinity
  (`0.2402` vs `0.2747 PSU`), and TEOS-10 sound speed (`2.8258` vs
  `3.5719 m/s`).
- Re-ran notebook `6` as a Python export after the validation run; chart
  PNG/SVG outputs now have fresh timestamps and use the finalized raw-support
  contour thresholds `W_raw=6` and `W_raw=30`. This chart/product-cache rerender
  completed in `16.77` seconds on `galatea`.

## Validation Targets

Focused tests should prove:

- component variances are added in variance space;
- pressure-gradient variance is `(gradient * pressure_error)^2`;
- weighted aggregate variance uses `sum(alpha_i^2 var_i)`, not
  `sum(w_i^2 var_i) / sum(w_i^2)`;
- `var_spatial` is added as a separate T/S model bucket before sound-speed
  propagation;
- `cov_TS` is zero and no cross term is included;
- sigma outputs are square roots of stored variances.
