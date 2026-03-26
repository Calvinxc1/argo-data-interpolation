# Uncertainty Notes: Argo Cycle Representation

These notes cover uncertainty decomposition, sensor-error conventions, and the query-time storage or memory implications of the current vertical representation pipeline. Source-backed claims in this file should trace to [../literature-review.md](../literature-review.md).

## Query-time storage and memory implications

Every interpolating method (Reiniger-Ross, Akima, PCHIP, MRST-PCHIP) shares a structural property: the full profile must be retained in memory at query time because the interpolant is defined by the positions of the observations. This pipeline does not share this requirement. In this pipeline design, once the spline is fit, the raw data can be discarded entirely.

**Reiniger-Ross:** Fit cost: none. Direct interpolation with no fitting step. Memory at query time: full profile retained, roughly 10 to 30 KB per cycle as floating-point arrays.

**Akima:** Fit cost: O(n), computes slopes at every point using five nearest neighbors, then constructs cubic coefficients per interval. Memory: original observations plus polynomial coefficients per interval, roughly four to five floats per interval. Full pressure grid must be retained.

**PCHIP:** Fit cost: O(n), slope computation and cubic coefficients per interval. Memory: same structure as Akima.

**MRST-PCHIP:** Fit cost: O(17n), sixteen PCHIP passes plus a final mapping pass. Memory: full SA and CT arrays required to reconstruct the interpolation coordinate system. No compression possible.

**This pipeline:** Fit cost: two Savitzky-Golay filter passes plus peak detection plus one LSQ solve, O(n x k^2) where k is knot count (5 to 11). Memory at query time: approximately 280 bytes per variable per cycle versus 10 to 30 KB for any interpolating method. Compression ratio roughly 40 to 100 to 1.

| Method | Fit cost | Query memory | Compresses? |
|---|---|---|---|
| Reiniger-Ross | None | Full profile (~10-30 KB) | No |
| Akima | O(n) | Full profile + coefficients | No |
| PCHIP | O(n) | Full profile + coefficients | No |
| MRST-PCHIP | O(17n) | Full SA + CT arrays | No |
| This pipeline | O(n) + LSQ | ~280 bytes per variable | Yes, ~40-100x |

The memory argument is particularly sharp. Once any interpolating method's raw profile is discarded, the interpolant no longer exists. Once this pipeline's spline is stored, the raw profile can be discarded permanently and the full queryable model is preserved in approximately 280 bytes.

## Uncertainty quantification as a differentiator

Most operational methods produce no per-profile uncertainty estimate. Reiniger-Ross, Akima, PCHIP, and MRST-PCHIP are pure interpolation methods returning a value at a queried depth with no attached confidence interval and no indication of whether that depth is in a noisy thermocline or a stable deep layer.

Gridded products do produce uncertainty estimates, EN4 being the most notable. But those uncertainties reflect horizontal mapping error, the uncertainty from interpolating spatially across sparse float coverage. They do not reflect uncertainty in the vertical representation of any individual profile, and they do not vary with depth in a physically motivated way.

Kuusela and Stein (2018) and Park et al. (2023) represent the frontier of principled uncertainty quantification in Argo analysis, using full GP frameworks that propagate covariance through the spatiotemporal estimation. But again, those uncertainties describe the horizontal mapping problem, not the vertical profile representation problem.

This pipeline produces something none of those methods offer: a depth-varying uncertainty estimate for an individual profile's vertical representation, grounded in three physical sources of error.

The spline reconstruction residual (`cycle_rmse`) captures how well the compressed representation fits the raw observations. Constant across depths for a given cycle.

The sensor noise floor (0.002 C for temperature, 0.01 PSU for salinity) captures the irreducible measurement uncertainty from the SBE-41 CTD. Also constant across depths.

The pressure sensor error propagated through the local temperature gradient (`|dT/dP| x 2.4`) is the depth-varying component. In the thermocline where `dT/dP` can reach 0.1 C/dbar, a 2.4 dbar pressure uncertainty contributes up to 0.24 C of temperature uncertainty. In the flat deep ocean where `dT/dP` approaches zero, this term vanishes.

The result is that total uncertainty is largest precisely where the ocean is most variable and hardest to represent accurately, and smallest where the profile is most stable. This follows directly from the physics of the measurement.

## Sensor error: Wong et al. and Barker et al.

### Official uncertainty specifications

| Sensor | Float type | PRES error | TEMP error | PSAL error |
|---|---|---|---|---|
| SBE CTD standard | APEX, NAVIS (0-2000 dbar) | 2.4 dbar (constant) | 0.002 C | max(adjustment uncertainty, 0.01) PSU |
| SBE CTD Deep-Argo | SBE-41CP, SBE-61 (0-6000 dbar) | (2.5/6000) x PRES + 2 | 0.002 C | minimum 0.004 PSU |
| RBRargo3\|2K | RBR (0-2000 dbar) | 1 dbar (constant) | 0.002 C | max(propagated adjustment errors, 0.01) PSU |

The depth-dependent formula `(2.5/6000) x PRES + 2` applies only to Deep-Argo floats sampling beyond 2000 dbar. The pipeline's use of constant 2.4 dbar is exactly correct for standard SBE APEX and NAVIS floats at 0 to 2000 dbar.

Notable quirks: temperature error is 0.002 C universally across all float types with no exceptions. RBR pressure accuracy (1 dbar) is more than twice as good as SBE (2.4 dbar). The 0.01 PSU floor on standard Argo salinity cannot be undercut regardless of sensor stability.

### Barker et al. (2011): two distinct pressure error sources

**Systematic drift:** APEX float pressure sensors accumulated positive pressure bias over time. Array average around -2 dbar for 2003-era data, but individual floats could exceed 10 dbar. It caused overestimates of temperature at depth and errors in salinity, thermosteric sea level, and ocean heat content before corrections were applied.

**Residual measurement uncertainty:** The ±2.4 dbar figure is the manufacturer's accuracy specification for residual random uncertainty after drift correction has been applied. These are different quantities at different stages of the data chain.

For `DATA_MODE == "D"` profiles, the pressure drift correction has already been applied. The `PRES` column that `argopy` serves is `PRES_ADJUSTED`. The pipeline's use of ±2.4 dbar is therefore correct for the already-corrected `PRES` values.

### The OWC method and argopy's handling

The OWC method compares each float's potential temperature-salinity curves against historical climatological curves at nearby stable depth levels and corrects for conductivity sensor drift. OWC uncertainty estimates are profile-level scalars: a single adjusted error value per profile or per record segment. The error is not depth-varying within a profile.

`argopy` transparently serves `PSAL_ADJUSTED` as `PSAL` for `DATA_MODE == "D"` profiles. The `DATA_MODE` column is the key indicator. For historical data, all records should be `"D"`. Guard:

```python
print(data["DATA_MODE"].value_counts())
rt_count = (data["DATA_MODE"] == "R").sum()
if rt_count > 0:
    print(f"Warning: {rt_count} real-time profiles with uncorrected PSAL")
```

### TNPD: truncated negative pressure drift

APEX floats with Apf-5, Apf-7, or Apf-8 controllers truncated any negative surface pressure reading to zero before telemetry, masking negative drift entirely. The problem was compounded by Druck oil microleak failures after mid-2006: failure rate jumped from 3 percent to 30 percent, causing increasingly severe negative drift.

Observable signatures: positive apparent salinity drift, cold temperature anomaly proportional to vertical gradient, dynamic height anomaly lower than altimetry, shoaling of isotherm depths over time.

Affected profiles are flagged: `PRES_ADJUSTED_ERROR = 20` dbar for post-2006 Druck sensors with unknown negative drift. Profiles with observable T or S anomalies are flagged `QC = "4"` entirely.

Guard for the pipeline:

```python
data = data[data["PRES_ERROR"] < 10]
# PRES_ERROR == 2.4: standard or low-risk TNPD, safe to use
# PRES_ERROR == 20: suspected microleaker, unknown large negative drift, exclude
```
