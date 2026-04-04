# Jana Replication Notes: Underwater Acoustics

These working notes capture how the Jana et al. study can be used as the current downstream demonstration target for uncertainty-aware Argo profile interpolation. Source-backed claims in this file trace to [../literature-review.md](../literature-review.md). Broader downstream-model or package-specific statements that are not yet in the literature review are marked as proposal-level recommendations or future validation work.

## Citation

Jana, S., Gangopadhyay, A., Haley, P. J., Jr., and Lermusiaux, P. F. J. (2022). *Sound speed variability over Bay of Bengal from Argo observations (2011-2020).* In *OCEANS 2022, Hampton Roads* (pp. 1-7). IEEE. DOI: `10.1109/OCEANSChennai45887.2022.9775509`

## Source-backed summary

Jana et al. (2022) is currently the cleanest verified anchor for this topic because it uses public Argo observations, converts temperature and salinity to sound speed, interpolates the resulting profiles to a uniform 1 m grid from 5 m to 500 m, and analyzes outputs that matter acoustically, including sound-speed variability structure and sonic-layer-related interpretation.

The paper's retained dataset size, filtering rules, and deterministic profile-processing sequence make it suitable for a like-for-like replication baseline. The strongest verified reason to use it is not that it is the most sophisticated acoustic study, but that it exposes a narrow, reproducible Argo-to-sound-speed workflow where interpolation choices are visible and downstream interpretation remains understandable. It is also a short IEEE OCEANS conference paper with a very compressed methods section, which is why several replication choices below remain explicitly interpretive rather than directly source-stated.

## Inference

This study is a better initial showcase than a full uncertainty-aware acoustic-propagation paper because it isolates the exact stage where the current package aims to contribute. The project does not need to invent a new acoustic solver to demonstrate value. It can first show that the interpolation step itself can emit a sound-speed profile with explicit uncertainty structure instead of a silent point estimate.

The most defensible extension path is:

1. Reproduce the Jana baseline outputs as closely as practical.
2. Replace the deterministic profile gridding step with PCHIP and/or smoothing-spline variants that emit per-level uncertainty estimates.
3. Quantify how those uncertainty estimates affect derived sound-speed structure, sonic layer depth identification, and any downstream acoustic diagnostic added in the extension study.

## Recommendation

The replication should keep one strong baseline path that stays as close as possible to Jana et al., including the original sound-speed equation if needed for a strict comparison. A second path can then introduce the TEOS-10/GSW sound-speed calculation as an explicit upgrade so interpolation effects and equation-of-state effects are not conflated in the first comparison.

The current project story is strongest if it shows two things separately:

- changing the interpolation method changes the gridded sound-speed structure in physically meaningful regions such as sharp gradients and sonic-layer-relevant depths
- attaching uncertainty at the interpolation stage gives the downstream acoustic workflow information it did not previously have

## Replication Method Notes

### Final Pipeline Settlement

The settled replication pipeline uses `argopy` standard mode with QC 1/2 filtering, whole-profile outlier dropping, a three-standard-deviation threshold, and extrapolation-enabled interpolation. These decisions were made after testing multiple variants against Jana et al.'s reported retained archive size of 14,246 profiles and against the paper's Figure 3 behavior.

### Decision

The outlier filter is applied at the whole-profile level, not per variable, because Jana et al. state that they "removed the profiles having data values outside two standard deviations from the mean profiles." In the replication, a cycle is dropped entirely if either temperature or salinity has any observation outside the selected standard-deviation threshold at any depth level.

The standard-deviation threshold is set to 3 rather than 2. A literal 2-SD implementation drove the combined retained count down to about 8,965, a gap of roughly 38% from Jana et al.'s reported 14,246 that was not methodologically defensible as simple dataset drift. With a 3-SD threshold the combined retained set is 13,400 linear cycles, a gap of about 6%, and the resulting Figure 3 diagnostics match the paper's reported values closely enough to support that empirical calibration. This threshold change is therefore treated as an empirical replication adjustment rather than a literal paper method.

Extrapolation is enabled on the interpolation wrappers. Jana et al. define a 5 m to 500 m analysis grid while requiring only one observation shallower than 20 m, which implies some near-surface extrapolation when a retained profile does not contain an observation exactly at or above 5 m. Disabling extrapolation produced `NaN` values in the 5 m to 20 m range, which then distorted the outlier filter and artificially reduced the retained cycle count.

This replication still uses the standard `argopy` fetch path rather than an explicit delayed-mode-only workflow. Practically, this means the notebook is operating on the standard-mode merged `PRES`, `TEMP`, and `PSAL` product exposed by `argopy`.

### Final Confirmed Pipeline

1. Pull `argopy` standard-mode data for 80 to 99 degrees east, 6 to 23 degrees north, 0 to 750 dbar, and 2011-01-01 through 2020-12-31.
2. Apply QC flag filtering that retains flags 1 and 2 only.
3. Retain only cycles with at least one observation shallower than 20 m and at least one observation at or below 500 dbar.
4. Resolve within-cycle duplicate pressure observations before fitting; the current notebook does this with `ModelData.clean_duplicates('mean')`, which averages duplicated pressure rows inside a cycle.
5. Convert pressure to depth in meters using `gsw.z_from_p(pressure, latitude)` with the recorded latitude of each cycle.
6. Interpolate to a regular 1 m grid from 5 m to 500 m inclusive using the linear baseline, with extrapolation enabled so the 5 m to 20 m interval can be filled when a retained profile has only one observation shallower than 20 m.
7. Compute mean and standard deviation at each 1 m depth level across all cycles independently for temperature and salinity.
8. Apply a two-sided three-standard-deviation outlier filter independently to temperature and salinity.
9. Drop the full cycle if either temperature or salinity has any depth level with `abs(z) >= 3`.
10. Proceed with the surviving combined cycle set for sound-speed computation and aggregate statistics.

### Pressure Conversion Bug Fix

One notebook bug was identified in the pressure-grid construction for the interpolated profiles. Passing the index directly into the `pd.Series` constructor caused a misalignment between the `gsw.p_from_z(...)` output and the intended depth index. The fix was to construct the series first and assign the index afterward:

```python
pressure_increments = pd.Series(gsw.p_from_z(-depth_increments, latitude), name=cycle_id)
pressure_increments.index = depth_increments
```

### Final Cycle Counts

| Filter applied | Linear | PCHIP |
| --- | ---: | ---: |
| Temperature only | 14,506 | 14,472 |
| Salinity only | 14,150 | 14,161 |
| Both temperature and salinity | 13,400 | 13,396 |
| Either temperature or salinity | 15,256 | 15,237 |

Jana et al. report 14,246 cycles. The working dataset for subsequent analysis is the combined linear count of 13,400 cycles. This is 846 cycles below the paper's reported total, roughly 5.9%, which remains plausible as a dataset-drift effect between the study's 2022 IFREMER Coriolis FTP snapshot and the current `argopy` ERDDAP pull.

### Interpretive Rationale

- Pull depth 750 dbar: avoids truncating profiles before the 500 dbar retention test is applied.
- Depth filter in dbar rather than meters: 500 m converts to roughly 503.5 dbar, which exceeds the maximum observed profile depth in this dataset and makes a strict meter-based threshold impractical.
- Upper 20 m filter: this is explicitly stated in Jana et al., which says that profiles with at least one observation within the upper 20 m and extending to 500 m and beyond were retained.
- Linear interpolation: Jana et al. do not specify the interpolation method, so linear remains the most conservative and simplest replication baseline.
- Per-profile latitude in `gsw.z_from_p`: the conversion is more defensible when it uses each cycle's recorded latitude rather than a single representative domain latitude.
- Extrapolation in the 5 m to 20 m range: Jana et al. define a 5 m to 500 m grid while only requiring one observation shallower than 20 m, so some extrapolation near the surface is implicit in their stated workflow.
- Single-pass outlier filter: Jana et al. do not describe iterative trimming, so single-pass is the simpler reading of the paper.
- Whole-profile dropping: Jana et al. say they removed "the profiles," which is more naturally read as dropping the full cycle once either temperature or salinity violates the threshold.
- Three-standard-deviation threshold: this is an empirical replication adjustment rather than a literal paper method. It is retained because 2 SD produced an implausibly small archive and because the 3-SD Figure 3 diagnostics align closely with the published values.
- OR logic across depth levels: a single exceedance is enough to flag the profile as anomalous under the paper's phrasing about removing profiles with values outside the threshold.
- Filter after interpolation: this creates a common depth axis for profile-to-profile comparison and matches the paper's interpolation-then-filter ordering.
- Standard mode without delayed-mode filtering: Jana et al. do not mention delayed-mode-only selection, and the delayed-mode-filtered variants were less reproducible across reruns.

### Sound Speed Computation

Sound speed is computed with `seawater.svel(salinity, temperature, pressure)` from the `seawater` library. This library implements the Chen and Millero (1977) / UNESCO 1983 sound-speed formulation and is kept despite the library's deprecation warning because it likely matches Jana et al.'s implementation more closely than the modern TEOS-10 `gsw` formulation. The current saved notebook imports `seawater` directly and therefore still shows the library deprecation warning in its recorded output; warning suppression is not part of the saved notebook state.

### Working Data Structures

The notebook now carries the active retained set in wide-format dataframes with depth in meters as the index and cycle IDs as the columns:

- `temp_active_profiles`: temperature in degrees Celsius
- `sal_active_profiles`: salinity in PSU
- `pres_active_profiles`: pressure in dbar after conversion from the shared depth grid using `gsw.p_from_z`
- `sound_speed_profiles`: sound speed in meters per second from `sw.svel`

Cycle metadata for the working retained set are stored in `active_cycles_metadata`. The metadata fields are latitude, longitude, timestamp, and month, with month encoded as an ordered categorical from January through December.

### Subdomain Definitions

The current notebook encodes the Jana et al. subdomains as:

| Subdomain | Longitude | Latitude | Description |
| --- | --- | --- | --- |
| BoB | 80 to 99 degrees east | 6 to 23 degrees north | Entire domain |
| N-BoB | 86 to 93 degrees east | 16 to 21 degrees north | Northern Bay of Bengal |
| C-BoB | 86 to 93 degrees east | 11 to 16 degrees north | Central Bay of Bengal |
| S-BoB | 86 to 93 degrees east | 6 to 11 degrees north | Southern Bay of Bengal |
| CW-BoB | 80.5 to 86 degrees east | 12 to 18 degrees north | Central western Bay of Bengal |
| SW-BoB | 80.5 to 86 degrees east | 6 to 12 degrees north | Southwestern Bay of Bengal |
| AS | 93 to 98 degrees east | 8 to 14 degrees north | Andaman Sea |

### Figure 3 Validation

The current Figure 3 replication matches Jana et al.'s published structure closely enough to support the settled pipeline:

- sound-speed standard deviation at 35 m: 2.14 m/s versus their approximately 2.4 m/s
- sound-speed standard deviation at 110 m: 5.25 m/s versus their approximately 6.0 m/s
- surface sound-speed standard deviation at 5 m: 2.69 m/s versus their approximately 3.0 m/s

The qualitative shape of the profile is essentially identical to Jana et al.'s Figure 3. The remaining amplitude differences are consistent with expected dataset differences.

### Spatial Grid Aggregation

Figures 4 and 5 use a 2 degree by 2 degree spatial kernel evaluated at each 1 degree grid point across the 80 to 99 degrees east, 6 to 23 degrees north domain. Grid points are retained only if they contain data from all 12 months and at least 30 total values, matching Jana et al.'s stated criteria. Under the current retained archive this produces 165 valid grid points out of 360 possible positions, which the notebook now prints explicitly as 45.8% coverage and 195 missing grid points. Missing cells are concentrated in the Andaman Sea, northern coastal regions, and land-boundary-adjacent areas.

Grid-point coordinates are stored as string keys in the form `"{lat}-{lon}"` and used as dataframe column labels. The aggregated gridded outputs are:

- `temp_mean_grid` and `temp_stdev_grid`
- `sal_mean_grid` and `sal_stdev_grid`
- `spd_mean_grid` and `spd_stdev_grid`

Each dataframe uses depth in meters as the index and grid-point keys as the columns.

The notebook now also includes a `figure45_summary` audit dataframe that records min and max values at 5 m, 35 m, 110 m, and 500 m for each Figure 4 and Figure 5 grid product.

### Figures 4 and 5 Validation

The spatial patterns in Figures 4 and 5 are qualitatively consistent with Jana et al.'s reported maps.

Figure 4, temporal mean:

- Temperature shows warmer values in the south at the surface with cooling toward the north, then a reversal of structure at thermocline depths.
- Salinity shows strong freshening in the northern Bay of Bengal at the surface, with saltier water throughout the domain at depth.
- Sound speed follows temperature dominance and shows lower values in the fresher northern surface layer.

Figure 5, temporal standard deviation:

- Temperature standard deviation is highest in the northern Bay of Bengal at the surface and shifts toward the western boundary around 110 m thermocline depth.
- Salinity standard deviation is largest at the surface in the northern Bay of Bengal and collapses to near zero by 500 m.
- Sound-speed standard deviation follows temperature dominance at 110 m, with the western boundary showing the highest variability.

The remaining magnitude differences between the replication and Jana et al. are consistent with the reduced retained cycle count and broader dataset differences documented above.

### Figures 6 Through 11 Validation

The current notebook now generates Figures 6 through 11 as month-depth composite plots for the six Jana et al. subdomains. Each figure contains three panels: month-depth mean, month-depth standard deviation, and month-depth mean vertical gradient of sound speed.

Visual inspection of the saved figures suggests the following broad qualitative matches to Jana et al.:

- `N-BoB`: a strong spring sound-speed-variability feature near the thermocline, with a second later-season enhancement and a pronounced winter near-surface gradient structure.
- `C-BoB`: weaker variability structure than the northern and western subdomains, broadly consistent with the paper's interpretation of reduced direct boundary-current and freshwater influence.
- `S-BoB`: dual variability structures in the thermocline and a pattern consistent with stronger southern or equatorial influence.
- `CW-BoB`: strong thermocline variability concentrated in spring and late summer.
- `SW-BoB`: a later post-monsoon variability maximum, consistent with the timing Jana et al. describe.
- `AS`: noisier but still physically interpretable structure, consistent with sparser profile coverage.

These subdomain figures use fixed colorbar ranges in the notebook for comparability across panels: mean `1500` to `1545 m/s`, standard deviation `0` to `8 m/s`, and mean vertical gradient `-0.6` to `0.4 m/s per meter`.

### Reproducibility Notes

Jana et al. provide no public code repository, and the methods section is extremely compressed relative to the amount of data processing implied by the study. Several implementation choices in the notebook therefore remain explicit replication interpretations rather than direct paper transcriptions:

- interpolation method: the paper does not specify the method, so the notebook uses the local `LinearAdapter` as the primary linear baseline and compares it with PCHIP
- standard-deviation threshold: the paper states 2 SD, but the replication uses 3 SD as an empirical calibration to recover plausible retained counts and Figure 3 behavior
- outlier-filter scope: the notebook implements whole-profile dropping after initially testing narrower per-variable policies
- depth threshold handling: the 500 m requirement is implemented against pressure in dbar because the practical conversion to meters overshoots the available profile maximum in the pulled dataset
- extrapolation: not stated in the paper, but enabled in the notebook to make the 5 m grid start compatible with the shallower-than-20 m inclusion rule
- data mode: not stated in the paper, so the notebook settles on `argopy` standard mode because it is the most stable and closest practical match among the tested pull configurations

The inability to recover every methodological detail directly from the paper is one of the clearest motivations for keeping the extension study transparent about interpolation policy, validation choices, and uncertainty propagation.

### Next Steps

1. Place the Jana replication back into the broader NASCar / regional acoustics trajectory so the replication sits inside the larger research narrative rather than as a standalone notebook artifact.
2. Build the uncertainty-aware extension by replacing the deterministic interpolation step with uncertainty-emitting linear, PCHIP, and spline variants, then propagate those profile uncertainties through the UNESCO sound-speed calculation and into derived diagnostics such as sonic-layer depth.

### Notebook Alignment Check

The saved `jana-study-replication.ipynb` notebook now matches this settled pipeline on the substantive steps:

- standard-mode pull with no explicit delayed-mode filter
- QC 1/2 filtering on `PRES_QC`, `TEMP_QC`, and `PSAL_QC`
- upper-20 m and 500 m retention filters
- duplicate-pressure cleanup with `clean_duplicates('mean')` before model fitting
- extrapolation-enabled linear and PCHIP interpolation wrappers
- 5 m through 500 m inclusive interpolation grid
- per-profile latitude in the pressure-to-depth conversion
- whole-profile screening with `sd_val = 3`
- final cycle counts of 14,506 / 14,150 / 13,400 / 15,256 for linear and 14,472 / 14,161 / 13,396 / 15,237 for PCHIP
- sound-speed computation through `sw.svel`
- printed spatial-grid coverage of `165 / 360` valid grid points plus the `figure45_summary` audit table
- subdomain Figure 6 through Figure 11 generation with fixed colorbar defaults of `1500` to `1545`, `0` to `8`, and `-0.6` to `0.4`

Two implementation details remain worth noting: the current linear baseline in code is the local `LinearAdapter`, which uses a linear spline representation (`k=1`) rather than a direct `scipy.make_interp_spline` call, and the saved notebook still records the `seawater` deprecation warning rather than suppressing it.

## Implementation assumption

The likely first downstream acoustic extension is a simple deterministic propagation workflow run repeatedly over an ensemble of uncertainty-aware sound-speed profiles rather than a bespoke stochastic acoustic solver. That choice is an implementation strategy for the package demonstration, not yet a source-backed claim for this topic.

## Future validation work

- Verify primary-source details for the acoustic model or wrapper selected for the downstream extension.
- Determine whether the Jana workflow's exact interpolation method can be confirmed from paper text, supplementary material, or reproducible code.
- Add source-backed coverage for any acoustic-metric sensitivity claims before using them in canonical writing.
