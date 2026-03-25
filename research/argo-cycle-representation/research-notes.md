# Pipeline Notes: Argo Cycle Representation

Working notes on how the published vertical interpolation literature relates to this pipeline, including comparisons, competitive advantages, implementation details, and planned experiments.

---

## Barker and McDougall (2020): MRST-PCHIP comparison

### What they are solving vs. what this pipeline solves

Barker and McDougall are solving a different problem. Their goal is to interpolate between observed data points on a single profile, producing values at arbitrary intermediate pressures while preserving physically realistic water-mass structure. The profile is assumed to be fully retained in memory. Nothing is compressed or discarded.

This pipeline is solving a representation problem. The goal is to produce a compact, queryable model of the vertical structure of each profile that can replace the raw observations entirely. The pipeline is not designed to pass through every observation. It is designed to capture the large-scale structure faithfully while discarding fine-scale noise, and to do so with a minimal number of parameters.

These are related but distinct problems. MRST-PCHIP cannot be used for compression because it requires the full original profile to be stored. This pipeline cannot be used as a drop-in replacement for MRST-PCHIP in contexts requiring exact reproduction of observed values.

### The Gibbs ringing problem

Barker and McDougall motivate their work partly by demonstrating that cubic splines produce Gibbs ringing at sharp features like thermocline boundaries and mixed-layer bases. The overshoot is a mathematical consequence of the interpolating constraint: because the spline is forced to pass exactly through every observation, it must bend sharply to accommodate transitions, and that bending propagates into adjacent intervals as oscillation.

For exact cubic interpolants, this is not simply a tuning issue. Barker and McDougall (2020) document the overshoot problem empirically in oceanographic interpolation, and Zhang and Martin (1997) show for discontinuous functions on uniform meshes that maximum cubic-spline overshoot does not decrease with mesh refinement.

The LSQ spline in this pipeline should be less prone to this problem. It minimizes squared error across all observations without being constrained to pass through any of them. At a sharp thermocline transition, the spline should tend to find the best-fit smooth curve through the neighborhood of points rather than being forced through each one individually. Adding more knots in regions of high curvature, which curvature-based detection does automatically, should provide additional local flexibility to represent sharp features without oscillation.

### Noise sensitivity

Because MRST-PCHIP interpolates exactly, every observation is treated as ground truth. A sensor noise spike, an internal wave heave artifact, or a fine-scale salinity intrusion that happens to fall at a sampling depth is honored by the interpolant as real ocean structure. The effect propagates into adjacent intervals and cannot be removed without re-running the interpolation on cleaned data.

This pipeline is designed to reduce noise sensitivity at two separate stages.

First, the Savitzky-Golay smoothing pass before knot detection separates the noise signal from the structural signal before any fitting occurs. Noise spikes should be much less likely to generate curvature peaks on the smoothed profile, so knots should be less likely to be placed at noise artifacts.

Second, the LSQ solve minimizes squared error across all observations simultaneously. A single noisy point tends to be averaged down by its neighbors in the fit rather than pinned through. The resulting spline should represent the statistical center of the observation cloud around each pressure level rather than the exact value at any one of them.

The practical consequence is that this pipeline represents the large-scale gradient through a noisy thermocline by averaging across neighboring observations rather than honoring each sample exactly. Because MRST-PCHIP is still an exact interpolant, it may remain more sensitive to noisy samples than a least-squares representation, even though Barker and McDougall (2020) designed it to reduce overshoot and anomalous water-mass artifacts relative to earlier methods. This noise-sensitivity comparison is currently a hypothesis and should be tested directly rather than assumed.

### The knot placement distinction

MRST-PCHIP has no equivalent to knot placement. Every observation is a breakpoint and contributes equally to the interpolant structure regardless of whether it falls in a physically informative region.

This pipeline places knots where the profile is genuinely bending, using the second derivative of the smoothed profile as a physically motivated signal. The thermocline, where curvature is highest, receives the most knots. The flat deep ocean, where curvature is near zero, receives few or none. This means the model's degrees of freedom are concentrated where they earn the most representation fidelity, which is more efficient and more targeted to regions of high profile curvature than uniform breakpoint placement.

### Summary of comparative advantages

| Property | MRST-PCHIP | This pipeline |
|---|---|---|
| Passes through every observation | Yes (by design) | No |
| Noise sensitivity | Expected higher | Designed to be lower |
| Gibbs ringing at sharp features | Greatly reduced relative to cubic splines | Not imposed by exact interpolation |
| Compresses profile | No | Yes, ~9 knots on average |
| Queryable at arbitrary pressure | Yes, requires full profile in memory | Yes, from stored spline only |
| Physically motivated structure | SA-CT diagram preservation | Curvature-based knot placement |
| Interpolation-method uncertainty quantification | Not provided in the method paper | Pipeline-specific depth-varying estimate from pressure error propagation |
| Per-profile RMSE benchmark | Not reported in literature | 0.175°C (temp), 0.0295 PSU (sal), cross-validated |

### Citation note on Gibbs ringing

Barker and McDougall treat Gibbs ringing in cubic splines as established fact requiring no citation. For discontinuous functions, Zhang and Martin (1997, Journal of Computational and Applied Mathematics) show that complete cubic spline interpolation on uniform meshes exhibits Gibbs-type oscillation near the discontinuity and that the maximum overshoot does not decrease with mesh refinement. That is not a proof for ocean thermoclines specifically, but it is the closest clean mathematical result supporting the general warning about spline ringing near sharp transitions. The claim that cubic splines are no longer used in physical oceanography is Barker and McDougall's own statement based on community knowledge, not a reference to an external source.

For any presentation or manuscript, Barker and McDougall (2020) would be the appropriate reference for both the interpolating spline problem and the current operational standard.

### Important caveat for honest presentation

MRST-PCHIP optimizes explicitly for SA-CT diagram fidelity, preserving water-mass structure in thermohaline space. This pipeline does not optimize for this. Equivalent RMSE on held-out pressure levels does not guarantee equivalent water-mass fidelity. Any comparison presented in a manuscript or presentation should be explicit about what the RMSE comparison covers (reconstruction accuracy at withheld pressure levels) and what it does not cover (SA-CT diagram structure preservation). A reviewer familiar with Barker and McDougall (2020) will ask about this distinction.

---

## Li et al. (2005): cross-domain validation of the core technique

Note: the Li et al. (2005) citation metadata is verified, but some interpretive details in this section remain provisional pending full-text confirmation.

### Critical clarification

Li et al. (2005) is a computer-aided design paper with no oceanographic intent or application. The authors (Weishi Li, Shuhong Xu, Gang Zhao, Li Ping Goh) were engineers at the Institute of High Performance Computing in Singapore and Beijing University of Aeronautics and Astronautics, working on reverse engineering of physical objects. This is important framing: they are not prior art in oceanography. If the interpretation holds, they may amount to independent prior art for the mathematical technique, which would be a stronger claim.

### What problem they were actually solving

Their domain was fitting B-spline curves to dense, noisy 3D point clouds from laser scanners of physical objects, such as aircraft components and car body panels. The goal was to recover a clean parametric curve model from potentially millions of noisy surface measurements, using as few control points as possible while staying within an error tolerance.

### The four failure modes they identified in prior approaches

Existing methods did not separate noise from structure before placing knots. Computing curvature directly from raw noisy point clouds produces a curvature signal dominated by sensor noise rather than geometric structure, so prior methods placed knots at noise-driven spikes rather than real geometric features.

Existing methods used uniform or heuristic knot spacing that ignored local data complexity, wasting degrees of freedom in structurally unimportant areas and starving complex regions of needed flexibility.

Existing interpolating methods honored every noisy observation exactly, causing the fitted curve to chase noise artifacts rather than represent the underlying geometry.

Existing methods required the user to specify the number of knots in advance, which is problematic because the appropriate knot count depends on the complexity of the data, which varies across profiles and samples.

### Their algorithmic solution

Smooth the discrete curvature with a lowpass digital filter first, separating structural signal from noise. Then place knots proportional to the integral of that smoothed curvature, concentrating them in high-curvature regions and leaving flat regions sparse. Use LSQ spline fitting rather than exact interpolation so individual noisy points are averaged rather than honored. The knot count emerges from the data structure rather than being specified in advance.

### The structural isomorphism with this pipeline

| Li et al. (2005) | This pipeline |
|---|---|
| Dense noisy 3D point cloud from laser scanner | Discrete noisy pressure-temperature observations from Argo CTD |
| High-curvature surface regions (edges, corners) | Thermocline and halocline transitions |
| Flat smooth surface regions | Deep ocean and mixed layer |
| Lowpass filter on discrete curvature | Savitzky-Golay pre-smoothing pass |
| Integral-based knot placement | find_peaks on second derivative of smoothed profile |
| LSQ spline fitting | make_lsq_spline on uniform resampled grid |
| Compact parametric curve representation | Compact queryable spline model per cycle |

Two independent research groups, working in entirely different domains with different motivations and data types, appear to have arrived at essentially the same algorithmic solution. This suggests that the underlying mathematical problem may be the same: noisy data sampled from an unknown smooth function with mixed flat and sharp-gradient structure, where the goal is a compact representation faithful to the large-scale structure without contamination by noise.

If the full-text interpretation holds, Li et al. (2005) would provide independent validation that curvature-adaptive LSQ spline fitting is a natural and principled answer to this class of problem. The four failure modes they identified in prior CAD methods appear to map closely onto the failure modes of Reiniger-Ross, cubic splines, and exact-interpolation methods in oceanographic interpolation.

---

## Reiniger-Ross and Akima: method notes

### Reiniger-Ross (1968)

Note: Reiniger and Ross (1968) remains provisional pending full-text confirmation, so the discussion below should be treated as subject to revision if direct review of the original paper changes the interpretation.

The operational standard for the World Ocean Database and World Ocean Atlas for decades. At each interpolation point it uses the four nearest observations, two above and two below, to construct a local reference curve. It computes two parabolas, one through the three upper points and one through the three lower points, then takes a weighted average. The weights are determined by how well each parabola fits the observation it does not include.

The intuition is sensible: use more local information than linear interpolation while avoiding the global sensitivity of a full cubic spline. The critical flaw is in the weighting function, which contains a rational expression whose denominator can approach zero in certain data configurations, causing numerical instability and occasionally producing wildly unrealistic values. Barker and McDougall document this failure mode directly. Additionally, because it works in pressure space with uneven spacing, it behaves inconsistently across Argo's depth-varying sampling regimes.

### Akima (1970)

A piecewise cubic method whose distinctive feature is how it computes slopes at each data point. Rather than solving a global system of equations as natural cubic splines do, it computes slopes locally using only the five nearest points. The slope formula down-weights the influence of points whose adjacent slopes differ dramatically from the local average.

The practical effect is much greater resistance to overshoot than natural cubic splines. A large gradient change at one location does not propagate its influence far into neighboring intervals. Akima is also shape-preserving in tendency, meaning it rarely introduces oscillations between observations. Its weakness relative to PCHIP is that it is not strictly monotonicity-preserving: in genuinely monotonic regions it can still introduce small overshoots at individual points, whereas PCHIP guarantees no new extrema.

Wong, Johnson, and Owens (2003) used Akima interpolation to vertically interpolate historical bottle salinity data onto standard potential-temperature surfaces when constructing the θ-S climatology used for delayed-mode calibration.

### Relationship to this pipeline

Both Reiniger-Ross and Akima are exact interpolants and can be expected to share the same fundamental noise-sensitivity risk as PCHIP. None of them escape the exact-interpolation constraint that makes this risk difficult to avoid.

Akima has a philosophical similarity to this pipeline in that both use local reasoning rather than global constraints. But the distinction is fundamental. Akima asks: given that I must pass through every point, what is the smoothest local way to do so? This pipeline asks: given all these points, what is the best compact model of the underlying structure? These are different questions with different answers.

---

## Yarger et al. (2022): vertical representation step only

This section covers only the vertical representation component of Yarger et al. (2022). Broader spatiotemporal prediction issues are outside the scope of these notes.

### What their vertical step actually does (confirmed from full paper review)

Their mean estimation uses B-spline smoothing splines with 200 equispaced knots over [0, 2000] dbar, chosen at intervals near the size of Argo pressure uncertainties of 2.4 dbar. GCV is used for smoothing parameter selection, with smoothing parameters chosen as fixed ratios collapsed into a single 1D search over (10^-3, 10^7). The working within-profile correlation structure uses a Markovian form with τ=0.001, giving correlation approximately 0.951 for measurements 50 dbar apart. Bandwidth is hs=900 km spatial, hd=45.25 days temporal.

This is an equispaced, globally tuned design. There is no per-profile knot adaptation, no curvature-guided knot placement, and no two-pass noise separation.

### Where this pipeline improves on their vertical step

Their 200 equispaced knots over 2000 dbar equals one knot every 10 dbar, regardless of what the water column is doing. This pipeline, by contrast, places 9 to 16 knots total (modal approximately 9) with curvature-guided placement, concentrating degrees of freedom where d²T/dP² is large.

Their smoothing parameter selection collapses all components into a single 1D GCV search with fixed ratios. This pipeline instead selects independently per-profile and per-variable based on the actual curvature signal of that cycle, which should make it more adaptive to individual float behavior and ocean regime.

Their representation is not a standalone artifact. Querying their model at an arbitrary pressure requires the surrounding spatial model, the locally estimated FPC basis, and the score predictions. This pipeline instead stores only (t, c, k) plus scalar cycle_rmse, approximately 280 bytes, queryable with no surrounding context.

Their uncertainty is spatiotemporal, derived from the kriging covariance at the spatial modeling stage. Their framework achieves good aggregate coverage but is reported to be weaker at 20 to 200 dbar, precisely the thermocline region where this pipeline's pressure-propagated error term (|dT/dP| × 2.4) is largest and may be most physically meaningful.

Their Section 6 explicitly lists adaptive bandwidth selection and allowing scale parameters to change as a function of depth as future work. This pipeline can be read as implementing analogues of both ideas at the vertical level.

### Framing

Yarger et al. (2022) recognized the same fundamental insight: profiles should be treated as continuous functions of depth rather than fixed-level vectors. Their framework built this insight into a spatiotemporal kriging system. My reading is that this pipeline is an engineering completion of that insight at the vertical level, making the single-profile spline representation step adaptive, compressed, and physically grounded in its uncertainty decomposition. The two approaches are complementary.

### RMSE comparability: vertical fitting vs. spatiotemporal prediction

This distinction is critical for presenting the pipeline's 0.175°C RMSE correctly.

Yarger et al.'s spatiotemporal prediction RMSE (~0.50°C at 300 dbar) measures how well nearby profiles from other floats can predict a held-out profile. It includes real oceanographic variability not captured by local spatial models, measurement error, and vertical representation error all combined.

This pipeline's RMSE (0.175°C TEMP, 0.0295 PSU PSAL) is a within-profile vertical fitting residual. It measures how well the stored spline artifact reconstructs the original observations from a single cycle. It does not include spatiotemporal variability at all.

A direct RMSE comparison between the two would be methodologically invalid. A defensible framing is: Yarger et al.'s ~0.50°C at 300 dbar establishes the magnitude of real oceanographic signal present in the data. This pipeline's 0.175°C represents the noise floor introduced by the vertical representation step alone, well below the spatiotemporal variability that any downstream prediction scheme must still account for. A well-designed vertical representation should have a fitting error substantially smaller than the spatiotemporal prediction error.

---

## TO DO: understand the full Argo scientific analysis pipeline

The raw profile preservation vs. interpolation distinction implies a chain of processing steps between a float surfacing and a researcher using a gridded climate product. Interpolation method choices enter that chain at specific, identifiable points.

Understanding this in detail matters for two reasons. First, it determines exactly where this pipeline's artifacts would slot into operational use: a replacement for the interpolation step inside Roemmich and Gilson, an alternative input format for EN4 or ISAS, or a preprocessing step before GP-based spatiotemporal analysis. Second, knowing where QC flags, bias corrections, and delayed-mode processing enter the chain clarifies what state the data is in when it reaches the vertical representation step.

Recommended reading: Wong et al. (2020) for the delayed-mode QC pipeline, Roemmich and Gilson (2009) for how interpolation enters the standard-level gridded product, Argo data management documentation at https://argo.ucsd.edu/data/data-management/, and Yarger et al. (2022) Section 2.1 and 2.2 for a concise processing context overview from a statistical user's perspective.

Follow-up item for a future version: account for measurement-time lag within Argo profiles. In the current pipeline design, a profile is treated as effectively static over the interval between subsurface measurement and later surface/report time. This is a simplifying implementation assumption. A future version should evaluate whether the within-cycle temporal offset is large enough to affect interpolation quality or uncertainty, especially when combining the vertical artifact with downstream spatiotemporal modeling.

---

## Sensor error: Wong et al. and Barker et al.

Every interpolating method (Reiniger-Ross, Akima, PCHIP, MRST-PCHIP) shares a structural property: the full profile must be retained in memory at query time because the interpolant is defined by the positions of the observations. This pipeline does not share this requirement. In this pipeline design, once the spline is fit, the raw data can be discarded entirely.

**Reiniger-Ross:** Fit cost: none. Direct interpolation with no fitting step. Memory at query time: full profile retained, roughly 10 to 30 KB per cycle as floating point arrays.

**Akima:** Fit cost: O(n), computes slopes at every point using five nearest neighbors, then constructs cubic coefficients per interval. Memory: original observations plus polynomial coefficients per interval, roughly four to five floats per interval. Full pressure grid must be retained.

**PCHIP:** Fit cost: O(n), slope computation and cubic coefficients per interval. Memory: same structure as Akima.

**MRST-PCHIP:** Fit cost: O(17n), sixteen PCHIP passes plus a final mapping pass. Memory: full SA and CT arrays required to reconstruct the interpolation coordinate system. No compression possible.

**This pipeline:** Fit cost: two SG filter passes plus peak detection plus one LSQ solve, O(n·k²) where k is knot count (5 to 11). Memory at query time: approximately 280 bytes per variable per cycle versus 10 to 30 KB for any interpolating method. Compression ratio roughly 40 to 100 to 1.

| Method | Fit cost | Query memory | Compresses? |
|---|---|---|---|
| Reiniger-Ross | None | Full profile (~10-30 KB) | No |
| Akima | O(n) | Full profile + coefficients | No |
| PCHIP | O(n) | Full profile + coefficients | No |
| MRST-PCHIP | O(17n) | Full SA + CT arrays | No |
| This pipeline | O(n) + LSQ | ~280 bytes per variable | Yes, ~40-100x |

The memory argument is particularly sharp. Once any interpolating method's raw profile is discarded, the interpolant no longer exists. Once this pipeline's spline is stored, the raw profile can be discarded permanently and the full queryable model is preserved in approximately 280 bytes.

---

## Python implementations for comparison experiments

### Akima

`scipy.interpolate.Akima1DInterpolator` is the recommended implementation. It is built into scipy with no additional installation required and is the same algorithm referenced in the oceanographic literature.

```python
from scipy.interpolate import Akima1DInterpolator
akima = Akima1DInterpolator(pres, temp)
temp_interp = akima(query_pressures)
```

Scipy also exposes a modified variant (`method='makima'` added in scipy 1.13.0) which further reduces overshoot by modifying the weight computation. Worth including in the comparison for completeness.

### Reiniger-Ross

There is no dedicated Python implementation of Reiniger-Ross. The canonical implementation is in the R `oce` package as `oceApprox(method="reiniger-ross")`, callable from Python via `rpy2`. The GSW-MATLAB toolbox contains `gsw_rr68_interp_SA_CT`, callable from Python via `oct2py`.

For the comparison experiments, scipy's `PchipInterpolator` and `Akima1DInterpolator` are probably sufficient without needing Reiniger-Ross, which is largely a historical baseline.

### MRST-PCHIP proxy

`scipy.interpolate.PchipInterpolator` is plain PCHIP without the 16-rotation MR enhancement. It is an exact interpolant forced through every observation, which is the critical property shared with MRST-PCHIP that matters for the noise and spike injection experiments.

```python
from scipy.interpolate import PchipInterpolator
pchip = PchipInterpolator(pres, temp)
temp_interp = pchip(query_pressures)
```

Full MRST-PCHIP can be implemented directly from Barker and McDougall (2020). The core is 16 PCHIP calls on rotated coordinate systems averaged back to the original frame, using observation index rather than pressure as the independent variable. Estimated implementation effort is a few hours. The `gsw` Python package does not currently expose the interpolation functions.

---

## Quantitative comparison experiments

### Experiment 1: Noise injection test

Inject synthetic Gaussian noise at the Argo sensor spec level (0.002°C standard deviation for temperature) into random pressure levels of a held-out cycle. Run both PCHIP and this pipeline on the noisy version and measure reconstruction error against the clean original at all other pressure levels. The key metric is how much each method's RMSE degrades under noise.

```python
np.random.seed(42)
noise = np.random.normal(0, 0.002, size=len(temp))
temp_noisy = temp + noise

degradation_pchip = rmse_pchip_noisy - rmse_pchip_clean
degradation_spline = rmse_spline_noisy - rmse_spline_clean
```

### Experiment 2: Spike injection test

Inject a single large spike (0.5°C) at one pressure level in the thermocline. Measure how far the artifact propagates into adjacent depths in each method. PCHIP must honor the spike and the distortion bleeds into neighboring intervals. This pipeline absorbs it as a local residual without propagating it.

```python
temp_spiked = temp.copy()
spike_idx = np.argmin(np.abs(pres - 150))  # spike at 150 dbar
temp_spiked[spike_idx] += 0.5

adjacent_mask = (np.abs(pres - pres[spike_idx]) > 0) & \
                (np.abs(pres - pres[spike_idx]) <= 20)

propagation_pchip = rmse(pchip(pres[adjacent_mask]), temp[adjacent_mask])
propagation_spline = rmse(spline(pres[adjacent_mask]), temp[adjacent_mask])
```

### Experiment 3: Cross-validation holdout RMSE comparison

Extend the existing 5-fold cross-validation to also run PCHIP on the same holdout folds. This produces a true apples-to-apples RMSE comparison on the same data using the same validation framework. This is the most publishable comparison because it reports a per-profile RMSE benchmark that does not exist anywhere in the published literature.

```python
from scipy.interpolate import PchipInterpolator

for fold in range(5):
    train_idx, test_idx = fold_indices[fold]

    pchip = PchipInterpolator(pres[train_idx], temp[train_idx])
    rmse_pchip_fold = rmse(pchip(pres[test_idx]), temp[test_idx])

    spline = fit_spline(pres_uniform, temp_smooth_uniform, knots)
    rmse_spline_fold = rmse(spline(pres[test_idx]), temp[test_idx])
```

### Experiment 4: Pickled file size comparison

Measure the serialized file sizes of each method's stored representation per cycle across all 469 cycles.

```python
import pickle

pchip_storage = {'pres': pres, 'temp': temp}
spline_storage = {
    'temp_t': temp_spline.t, 'temp_c': temp_spline.c,
    'temp_k': temp_spline.k, 'temp_rmse': cycle_rmse,
    'sal_t': sal_spline.t, 'sal_c': sal_spline.c,
    'sal_k': sal_spline.k, 'sal_rmse': sal_rmse
}

def pickled_size(obj):
    return len(pickle.dumps(obj))

print(f"PCHIP storage: {pickled_size(pchip_storage)} bytes")
print(f"This pipeline: {pickled_size(spline_storage)} bytes")
print(f"Compression ratio: {pickled_size(pchip_storage) / pickled_size(spline_storage):.1f}x")
```

Run this across all 469 cycles and report mean, median, and range of compression ratios.

---

## Uncertainty quantification as a differentiator

Most operational methods produce no per-profile uncertainty estimate. Reiniger-Ross, Akima, PCHIP, and MRST-PCHIP are pure interpolation methods returning a value at a queried depth with no attached confidence interval and no indication of whether that depth is in a noisy thermocline or a stable deep layer.

Gridded products do produce uncertainty estimates, EN4 being the most notable. But those uncertainties reflect horizontal mapping error, the uncertainty from interpolating spatially across sparse float coverage. They do not reflect uncertainty in the vertical representation of any individual profile, and they do not vary with depth in a physically motivated way.

Kuusela and Stein (2018) and Park et al. (2023) represent the frontier of principled uncertainty quantification in Argo analysis, using full GP frameworks that propagate covariance through the spatiotemporal estimation. But again, those uncertainties describe the horizontal mapping problem, not the vertical profile representation problem.

This pipeline produces something none of those methods offer: a depth-varying uncertainty estimate for an individual profile's vertical representation, grounded in three physical sources of error.

The spline reconstruction residual (cycle_rmse) captures how well the compressed representation fits the raw observations. Constant across depths for a given cycle.

The sensor noise floor (0.002°C for temperature, 0.01 PSU for salinity) captures the irreducible measurement uncertainty from the SBE-41 CTD. Also constant across depths.

The pressure sensor error propagated through the local temperature gradient (|dT/dP| × 2.4) is the depth-varying component. In the thermocline where dT/dP can reach 0.1°C/dbar, a 2.4 dbar pressure uncertainty contributes up to 0.24°C of temperature uncertainty. In the flat deep ocean where dT/dP approaches zero, this term vanishes.

The result is that total uncertainty is largest precisely where the ocean is most variable and hardest to represent accurately, and smallest where the profile is most stable. This follows directly from the physics of the measurement.

---

## Evidence of the value of this work

### The Li et al. (2022) framing

Li et al. (2022) established that MRST-PCHIP is the most accurate vertical interpolation method currently available, recovering ocean heat content estimates 14% larger than those produced by linear interpolation over the 1956-2020 historical record. The absolute magnitude of that gap is 40 Zeta Joules, with a corresponding thermosteric sea level rise correction of 0.55 mm/yr.

Critically, the 14% figure is the gap between linear interpolation and MRST-PCHIP. It does not apply as a claim for this pipeline over MRST-PCHIP. Li et al. (2022) establishes vertical interpolation accuracy as a climate-relevant problem with quantified downstream consequences, which motivates getting profile representation right.

### The equivalence argument

If Experiment 3 demonstrates that this pipeline produces reconstruction RMSE equivalent to MRST-PCHIP on the same profiles, then the following claim is fully defensible: this pipeline matches the physical fidelity of the current community standard for vertical interpolation, which Li et al. (2022) established is the accuracy ceiling of observationally based ocean heat content estimation.

### The additional value beyond equivalence

Equivalence in reconstruction accuracy combined with superiority in other dimensions is the complete argument. Compression: 40 to 100x reduction in storage per profile per variable, with no retained raw data required at query time. Noise robustness: LSQ fitting averages over observations rather than honoring each one exactly, unlike all interpolating methods. Uncertainty quantification: depth-varying, physically decomposed, queryable from the stored artifact alone. Standalone queryability: arbitrary pressure queries from stored coefficients only, no original profile needed.

---

## Sensor error: Wong et al. and Barker et al.

### Official uncertainty specifications (Argo QC Manual Version 3.9, DOI: 10.13155/33951)

| Sensor | Float type | PRES error | TEMP error | PSAL error |
|---|---|---|---|---|
| SBE CTD standard | APEX, NAVIS (0-2000 dbar) | 2.4 dbar (constant) | 0.002°C | max(adjustment uncertainty, 0.01) PSU |
| SBE CTD Deep-Argo | SBE-41CP, SBE-61 (0-6000 dbar) | (2.5/6000)×PRES + 2 | 0.002°C | minimum 0.004 PSU |
| RBRargo3\|2K | RBR (0-2000 dbar) | 1 dbar (constant) | 0.002°C | max(propagated adjustment errors, 0.01) PSU |

The depth-dependent formula (2.5/6000)×PRES + 2 applies only to Deep-Argo floats sampling beyond 2000 dbar (Sections 2.6.2 and 3.10 of the QC Manual). The pipeline's use of constant 2.4 dbar is exactly correct for standard SBE APEX and NAVIS floats at 0 to 2000 dbar.

Notable quirks: temperature error is 0.002°C universally across all float types with no exceptions. RBR pressure accuracy (1 dbar) is more than twice as good as SBE (2.4 dbar). The 0.01 PSU floor on standard Argo salinity cannot be undercut regardless of sensor stability (Section 3.5.6).

### Barker et al. (2011): two distinct pressure error sources

**Systematic drift:** APEX float pressure sensors (Ametek, Druck, Paine) accumulated positive pressure bias over time. Array average around -2 dbar for 2003 era data, but individual floats could exceed 10+ dbar. It caused overestimates of temperature at depth and errors in salinity, thermosteric sea level, and ocean heat content before corrections were applied.

**Residual measurement uncertainty:** The ±2.4 dbar figure is the manufacturer's accuracy specification for residual random uncertainty after drift correction has been applied. These are different quantities at different stages of the data chain.

For DATA_MODE == 'D' profiles, the pressure drift correction has already been applied. The PRES column that argopy serves is PRES_ADJUSTED. The pipeline's use of ±2.4 dbar is therefore correct for the already-corrected PRES values.

### The OWC method and argopy's handling

The OWC method compares each float's potential temperature-salinity curves against historical climatological curves at nearby stable depth levels and corrects for conductivity sensor drift. OWC uncertainty estimates are profile-level scalars: a single adjusted error value per profile or per record segment. The error is not depth-varying within a profile.

Argopy transparently serves PSAL_ADJUSTED as PSAL for DATA_MODE == 'D' profiles. The DATA_MODE column is the key indicator. For historical data, all records should be 'D'. Guard:

```python
print(data['DATA_MODE'].value_counts())
rt_count = (data['DATA_MODE'] == 'R').sum()
if rt_count > 0:
    print(f"Warning: {rt_count} real-time profiles with uncorrected PSAL")
```

### TNPD: Truncated Negative Pressure Drift

APEX floats with Apf-5, Apf-7, or Apf-8 controllers truncated any negative surface pressure reading to zero before telemetry, masking negative drift entirely. The problem was compounded by Druck oil microleak failures after mid-2006 (serial numbers above 2324175, deployed after October 2006): failure rate jumped from 3% to 30%, causing increasingly severe negative drift.

Observable signatures: positive apparent salinity drift, cold temperature anomaly proportional to vertical gradient, dynamic height anomaly lower than altimetry, shoaling of isotherm depths over time.

Affected profiles are flagged: PRES_ADJUSTED_ERROR = 20 dbar for post-2006 Druck sensors with unknown negative drift (threshold chosen because -20 dbar produces approximately +0.01 PSU apparent salinity error). Profiles with observable T/S anomalies are flagged QC = '4' entirely.

Guard for the pipeline:

```python
data = data[data['PRES_ERROR'] < 10]
# PRES_ERROR == 2.4: standard or low-risk TNPD, safe to use
# PRES_ERROR == 20:  suspected microleaker, unknown large negative drift, exclude
```

Source: Argo QC Manual Version 3.9, Section 3.3.2, DOI: 10.13155/33951.
