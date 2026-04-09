# Method Comparison Notes: Argo Cycle Representation

These notes compare the current vertical representation pipeline to the main interpolation and representation references discussed in [../literature-review.md](../literature-review.md). They are intended as working interpretation and comparison notes rather than as a standalone source-backed review. Where local benchmark numbers or artifact-size estimates appear, they should be read as project context and cross-checked against the validation notebook rather than treated as literature claims.

Implementation caveat: several passages below describe the curvature-adaptive least-squares spline prototype that motivated the original method framing. That prototype should now be treated as historical method-development context unless the validation notebook demonstrates robust performance. See [curvature-adaptive-spline-negative-result.md](curvature-adaptive-spline-negative-result.md) for the negative-result framing and the distinction between that prototype and FITPACK smoothing splines through `scipy.interpolate.make_splrep`.

## Barker and McDougall (2020): MRST-PCHIP comparison

### What they are solving vs. what this pipeline solves

Barker and McDougall are solving a different problem. Their goal is to interpolate between observed data points on a single profile, producing values at arbitrary intermediate pressures while preserving physically realistic water-mass structure. The profile is assumed to be fully retained in memory. Nothing is compressed or discarded.

This pipeline is solving a representation problem. The goal is to produce a compact, queryable model of the vertical structure of each profile that can replace the raw observations entirely. The pipeline is not designed to pass through every observation. It is designed to capture the large-scale structure faithfully while discarding fine-scale noise, and to do so with a minimal number of parameters.

These are related but distinct problems. MRST-PCHIP cannot be used for compression because it requires the full original profile to be stored. This pipeline cannot be used as a drop-in replacement for MRST-PCHIP in contexts requiring exact reproduction of observed values.

### The Gibbs ringing problem

The source-backed spline-ringing discussion is summarized in [../literature-review.md](../literature-review.md). The comparison point for this pipeline is narrower: because the LSQ spline is not constrained to pass through every observation, it should be less exposed to the exact-interpolation overshoot mechanism discussed there.

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
| Compresses profile | No | Yes, via a compact spline artifact |
| Queryable at arbitrary pressure | Yes, requires full profile in memory | Yes, from stored spline only |
| Physically motivated structure | SA-CT diagram preservation | Curvature-based knot placement |
| Interpolation-method uncertainty quantification | Not provided in the method paper | Pipeline-specific depth-varying estimate from pressure error propagation |

### Important caveat for honest presentation

MRST-PCHIP optimizes explicitly for SA-CT diagram fidelity, preserving water-mass structure in thermohaline space. This pipeline does not optimize for this. Equivalent RMSE on held-out pressure levels does not guarantee equivalent water-mass fidelity. Any comparison presented in a manuscript or presentation should be explicit about what the RMSE comparison covers (reconstruction accuracy at withheld pressure levels) and what it does not cover (SA-CT diagram structure preservation). A reviewer familiar with Barker and McDougall (2020) will ask about this distinction.

## Li et al. (2005): cross-domain validation of the core technique

The source-backed summary of Li et al. (2005) is in [../literature-review.md](../literature-review.md). The note-level use here is interpretive: the paper functions as a cross-domain analogue for curvature-adaptive least-squares spline fitting rather than as direct oceanographic prior art.

### The structural isomorphism with this pipeline

| Li et al. (2005) | This pipeline |
|---|---|
| Dense noisy 3D point cloud from laser scanner | Discrete noisy pressure-temperature observations from Argo CTD |
| High-curvature surface regions (edges, corners) | Thermocline and halocline transitions |
| Flat smooth surface regions | Deep ocean and mixed layer |
| Lowpass filter on discrete curvature | Savitzky-Golay pre-smoothing pass |
| Integral-based knot placement | `find_peaks` on second derivative of smoothed profile |
| LSQ spline fitting | `make_lsq_spline` on uniform resampled grid |
| Compact parametric curve representation | Compact queryable spline model per cycle |

Two independent research groups, working in entirely different domains with different motivations and data types, appear to have arrived at essentially the same algorithmic solution. This suggests that the underlying mathematical problem may be the same: noisy data sampled from an unknown smooth function with mixed flat and sharp-gradient structure, where the goal is a compact representation faithful to the large-scale structure without contamination by noise.

Li et al. (2005) provides a strong cross-domain analogue suggesting that curvature-adaptive LSQ spline fitting is a natural answer to this class of problem. The four failure modes they identified in prior CAD methods also map closely onto the failure modes of Reiniger-Ross, cubic splines, and exact-interpolation methods in oceanographic interpolation, though that mapping is an interpretive comparison rather than a claim made by Li et al. themselves.

## Reiniger-Ross and Akima: relationship to this pipeline

The source-backed descriptions of Reiniger-Ross and Akima are summarized in [../literature-review.md](../literature-review.md). The comparison point here is how those exact interpolants differ from a compact least-squares representation.

Both Reiniger-Ross and Akima are exact interpolants and can be expected to share the same fundamental noise-sensitivity risk as PCHIP. None of them escape the exact-interpolation constraint that makes this risk difficult to avoid.

Akima has a philosophical similarity to this pipeline in that both use local reasoning rather than global constraints. But the distinction is fundamental. Akima asks: given that I must pass through every point, what is the smoothest local way to do so? This pipeline asks: given all these points, what is the best compact model of the underlying structure? These are different questions with different answers.

## Yarger et al. (2022): vertical representation step only

This section covers only the vertical representation component of Yarger et al. (2022). The lit review summarizes the source-backed description of that step, including the fixed equispaced-knot design, global smoothing-parameter search, and the authors' own future-work note on adaptivity. The comparison here is limited to what those choices imply for the current pipeline.

### Where this pipeline improves on their vertical step

Their 200 equispaced knots over 2000 dbar equals one knot every 10 dbar, regardless of what the water column is doing. This pipeline, by contrast, places 9 to 16 knots total (modal approximately 9) with curvature-guided placement, concentrating degrees of freedom where d2T/dP2 is large.

Their smoothing parameter selection collapses all components into a single 1D GCV search with fixed ratios. This pipeline instead selects independently per-profile and per-variable based on the actual curvature signal of that cycle, which should make it more adaptive to individual float behavior and ocean regime.

Their representation is not a standalone artifact. Querying their model at an arbitrary pressure requires the surrounding spatial model, the locally estimated FPC basis, and the score predictions. This pipeline instead stores only `(t, c, k)` plus scalar `cycle_rmse`, approximately 280 bytes, queryable with no surrounding context.

Their uncertainty is spatiotemporal, derived from the kriging covariance at the spatial modeling stage. Their framework achieves good aggregate coverage but is reported to be weaker at 20 to 200 dbar, precisely the thermocline region where this pipeline's pressure-propagated error term (`|dT/dP| x 2.4`) is largest and may be most physically meaningful.

### Framing

Yarger et al. (2022) recognized the same fundamental insight: profiles should be treated as continuous functions of depth rather than fixed-level vectors. Their framework built this insight into a spatiotemporal kriging system. My reading is that this pipeline is an engineering completion of that insight at the vertical level, making the single-profile spline representation step adaptive, compressed, and physically grounded in its uncertainty decomposition. The two approaches are complementary.

### RMSE comparability: vertical fitting vs. spatiotemporal prediction

Direct RMSE comparison between Yarger et al.'s spatiotemporal predictions and this pipeline's within-profile reconstruction residuals is methodologically invalid because the two procedures measure different tasks. That quantitative distinction belongs primarily in the validation notebook; the comparison point relevant here is narrower: Yarger's error metrics combine spatial prediction difficulty with vertical representation, while this pipeline's local benchmarks isolate the vertical representation step.
