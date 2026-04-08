# Uncertainty Notes: Argo Cycle Representation

These notes cover uncertainty decomposition, sensor-error conventions, and the query-time storage or memory implications of the current vertical representation pipeline. Source-backed claims in this file should trace to [../literature-review.md](../literature-review.md). The storage and computational estimates below are local analysis of the current pipeline and comparison implementations, not claims from the literature.

## Query-time storage and memory implications

Local computational-analysis note: this section estimates storage and query-time implications of different representations for the current project setup. It is intended as project analysis, not as a literature summary.

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

The literature-facing part of this distinction is summarized in [../literature-review.md](../literature-review.md): the reviewed interpolation methods do not provide standalone per-profile uncertainty, and Yarger et al. attach uncertainty to a broader spatiotemporal functional-kriging system rather than to a stored vertical artifact for a single profile. The note-level question here is what uncertainty decomposition the current pipeline should expose in response.

Local design interpretation: this pipeline is intended to produce a depth-varying uncertainty estimate for an individual profile's vertical representation, grounded in three physical sources of error. The numeric source terms below use values summarized in the lit review; the way they are combined here is a local modeling choice.

The spline reconstruction residual (`cycle_rmse`) captures how well the compressed representation fits the raw observations. Constant across depths for a given cycle.

The sensor noise floor (0.002 C for temperature, 0.01 PSU for salinity) captures the irreducible measurement uncertainty from the SBE-41 CTD. Also constant across depths.

The pressure sensor error propagated through the local temperature gradient (`|dT/dP| x 2.4`) is the depth-varying component. In the thermocline where `dT/dP` can reach 0.1 C/dbar, a 2.4 dbar pressure uncertainty contributes up to 0.24 C of temperature uncertainty. In the flat deep ocean where `dT/dP` approaches zero, this term vanishes.

The result is that total uncertainty is largest precisely where the ocean is most variable and hardest to represent accurately, and smallest where the profile is most stable. This follows directly from the physics of the measurement.

## Sensor-error implications for this pipeline

The source-backed sensor and QC conventions are summarized in [../literature-review.md](../literature-review.md). The implications for the current implementation are narrower:

- for standard delayed-mode SBE profiles at 0 to 2000 dbar, `2.4` dbar is the relevant residual pressure uncertainty after drift correction
- the salinity uncertainty described by OWC and delayed-mode QC is profile- or segment-level, so any depth-varying uncertainty term in this pipeline is a local modeling layer rather than a source-provided field
- suspected TNPD microleaker profiles with `PRES_ADJUSTED_ERROR = 20` dbar should be excluded from routine use rather than treated as ordinary delayed-mode profiles

### Local data-loading assumptions

Implementation note: if the local data-loading layer aliases delayed-mode adjusted salinity into the working salinity field, the `DATA_MODE` column remains the key indicator. Verify the behavior of the specific client library in use before relying on that aliasing rule operationally. Guard:

```python
print(data["DATA_MODE"].value_counts())
rt_count = (data["DATA_MODE"] == "R").sum()
if rt_count > 0:
    print(f"Warning: {rt_count} real-time profiles with uncorrected PSAL")
```

### Guard for TNPD-flagged profiles

```python
data = data[data["PRES_ERROR"] < 10]
# PRES_ERROR == 2.4: standard or low-risk TNPD, safe to use
# PRES_ERROR == 20: suspected microleaker, unknown large negative drift, exclude
```
