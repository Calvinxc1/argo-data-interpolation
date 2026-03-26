# Method Comparison Notes: Argo Cycle Representation

These notes compare the current vertical representation pipeline to the main interpolation and representation references discussed in [../literature-review.md](../literature-review.md). They are intended as working interpretation and comparison notes rather than as a standalone source-backed review.

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

Barker and McDougall treat Gibbs ringing in cubic splines as established fact requiring no citation. For discontinuous functions, Zhang and Martin (1997, *Journal of Computational and Applied Mathematics*) show that complete cubic spline interpolation on uniform meshes exhibits Gibbs-type oscillation near the discontinuity and that the maximum overshoot does not decrease with mesh refinement. That is not a proof for ocean thermoclines specifically, but it is the closest clean mathematical result supporting the general warning about spline ringing near sharp transitions. The claim that cubic splines are no longer used in physical oceanography is Barker and McDougall's own statement based on community knowledge, not a reference to an external source.

For any presentation or manuscript, Barker and McDougall (2020) would be the appropriate reference for both the interpolating spline problem and the current operational standard.

### Important caveat for honest presentation

MRST-PCHIP optimizes explicitly for SA-CT diagram fidelity, preserving water-mass structure in thermohaline space. This pipeline does not optimize for this. Equivalent RMSE on held-out pressure levels does not guarantee equivalent water-mass fidelity. Any comparison presented in a manuscript or presentation should be explicit about what the RMSE comparison covers (reconstruction accuracy at withheld pressure levels) and what it does not cover (SA-CT diagram structure preservation). A reviewer familiar with Barker and McDougall (2020) will ask about this distinction.

## Li et al. (2005): cross-domain validation of the core technique

Note: the Li et al. (2005) citation metadata is verified, but some interpretive details in this section remain provisional pending full-text confirmation.

### Critical clarification

Li et al. (2005) is a computer-aided design paper with no oceanographic intent or application. The authors were working on reverse engineering of physical objects. This matters for framing: they are not prior art in oceanography. If the interpretation holds, they may amount to independent prior art for the mathematical technique, which would be a stronger claim.

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
| Integral-based knot placement | `find_peaks` on second derivative of smoothed profile |
| LSQ spline fitting | `make_lsq_spline` on uniform resampled grid |
| Compact parametric curve representation | Compact queryable spline model per cycle |

Two independent research groups, working in entirely different domains with different motivations and data types, appear to have arrived at essentially the same algorithmic solution. This suggests that the underlying mathematical problem may be the same: noisy data sampled from an unknown smooth function with mixed flat and sharp-gradient structure, where the goal is a compact representation faithful to the large-scale structure without contamination by noise.

If the full-text interpretation holds, Li et al. (2005) would provide independent validation that curvature-adaptive LSQ spline fitting is a natural and principled answer to this class of problem. The four failure modes they identified in prior CAD methods appear to map closely onto the failure modes of Reiniger-Ross, cubic splines, and exact-interpolation methods in oceanographic interpolation.

## Reiniger-Ross and Akima: method notes

### Reiniger-Ross (1968)

Note: Reiniger and Ross (1968) remains provisional pending full-text confirmation, so the discussion below should be treated as subject to revision if direct review of the original paper changes the interpretation.

The operational standard for the World Ocean Database and World Ocean Atlas for decades. At each interpolation point it uses the four nearest observations, two above and two below, to construct a local reference curve. It computes two parabolas, one through the three upper points and one through the three lower points, then takes a weighted average. The weights are determined by how well each parabola fits the observation it does not include.

The intuition is sensible: use more local information than linear interpolation while avoiding the global sensitivity of a full cubic spline. The critical flaw is in the weighting function, which contains a rational expression whose denominator can approach zero in certain data configurations, causing numerical instability and occasionally producing wildly unrealistic values. Barker and McDougall document this failure mode directly. Additionally, because it works in pressure space with uneven spacing, it behaves inconsistently across Argo's depth-varying sampling regimes.

### Akima (1970)

A piecewise cubic method whose distinctive feature is how it computes slopes at each data point. Rather than solving a global system of equations as natural cubic splines do, it computes slopes locally using only the five nearest points. The slope formula down-weights the influence of points whose adjacent slopes differ dramatically from the local average.

The practical effect is much greater resistance to overshoot than natural cubic splines. A large gradient change at one location does not propagate its influence far into neighboring intervals. Akima is also shape-preserving in tendency, meaning it rarely introduces oscillations between observations. Its weakness relative to PCHIP is that it is not strictly monotonicity-preserving: in genuinely monotonic regions it can still introduce small overshoots at individual points, whereas PCHIP guarantees no new extrema.

Wong, Johnson, and Owens (2003) used Akima interpolation to vertically interpolate historical bottle salinity data onto standard potential-temperature surfaces when constructing the theta-S climatology used for delayed-mode calibration.

### Relationship to this pipeline

Both Reiniger-Ross and Akima are exact interpolants and can be expected to share the same fundamental noise-sensitivity risk as PCHIP. None of them escape the exact-interpolation constraint that makes this risk difficult to avoid.

Akima has a philosophical similarity to this pipeline in that both use local reasoning rather than global constraints. But the distinction is fundamental. Akima asks: given that I must pass through every point, what is the smoothest local way to do so? This pipeline asks: given all these points, what is the best compact model of the underlying structure? These are different questions with different answers.

## Yarger et al. (2022): vertical representation step only

This section covers only the vertical representation component of Yarger et al. (2022). Broader spatiotemporal prediction issues are outside the scope of these notes.

### What their vertical step actually does

Their mean estimation uses B-spline smoothing splines with 200 equispaced knots over [0, 2000] dbar, chosen at intervals near the size of Argo pressure uncertainties of 2.4 dbar. GCV is used for smoothing parameter selection, with smoothing parameters chosen as fixed ratios collapsed into a single 1D search over (10^-3, 10^7). The working within-profile correlation structure uses a Markovian form with tau = 0.001, giving correlation approximately 0.951 for measurements 50 dbar apart. Bandwidth is hs = 900 km spatial and hd = 45.25 days temporal.

This is an equispaced, globally tuned design. There is no per-profile knot adaptation, no curvature-guided knot placement, and no two-pass noise separation.

### Where this pipeline improves on their vertical step

Their 200 equispaced knots over 2000 dbar equals one knot every 10 dbar, regardless of what the water column is doing. This pipeline, by contrast, places 9 to 16 knots total (modal approximately 9) with curvature-guided placement, concentrating degrees of freedom where d2T/dP2 is large.

Their smoothing parameter selection collapses all components into a single 1D GCV search with fixed ratios. This pipeline instead selects independently per-profile and per-variable based on the actual curvature signal of that cycle, which should make it more adaptive to individual float behavior and ocean regime.

Their representation is not a standalone artifact. Querying their model at an arbitrary pressure requires the surrounding spatial model, the locally estimated FPC basis, and the score predictions. This pipeline instead stores only `(t, c, k)` plus scalar `cycle_rmse`, approximately 280 bytes, queryable with no surrounding context.

Their uncertainty is spatiotemporal, derived from the kriging covariance at the spatial modeling stage. Their framework achieves good aggregate coverage but is reported to be weaker at 20 to 200 dbar, precisely the thermocline region where this pipeline's pressure-propagated error term (`|dT/dP| x 2.4`) is largest and may be most physically meaningful.

Their Section 6 explicitly lists adaptive bandwidth selection and allowing scale parameters to change as a function of depth as future work. This pipeline can be read as implementing analogues of both ideas at the vertical level.

### Framing

Yarger et al. (2022) recognized the same fundamental insight: profiles should be treated as continuous functions of depth rather than fixed-level vectors. Their framework built this insight into a spatiotemporal kriging system. My reading is that this pipeline is an engineering completion of that insight at the vertical level, making the single-profile spline representation step adaptive, compressed, and physically grounded in its uncertainty decomposition. The two approaches are complementary.

### RMSE comparability: vertical fitting vs. spatiotemporal prediction

This distinction is critical for presenting the pipeline's 0.175 C RMSE correctly.

Yarger et al.'s spatiotemporal prediction RMSE (approximately 0.50 C at 300 dbar) measures how well nearby profiles from other floats can predict a held-out profile. It includes real oceanographic variability not captured by local spatial models, measurement error, and vertical representation error all combined.

This pipeline's RMSE (0.175 C TEMP, 0.0295 PSU PSAL) is a within-profile vertical fitting residual. It measures how well the stored spline artifact reconstructs the original observations from a single cycle. It does not include spatiotemporal variability at all.

A direct RMSE comparison between the two would be methodologically invalid. A defensible framing is: Yarger et al.'s approximately 0.50 C at 300 dbar establishes the magnitude of real oceanographic signal present in the data. This pipeline's 0.175 C represents the noise floor introduced by the vertical representation step alone, well below the spatiotemporal variability that any downstream prediction scheme must still account for. A well-designed vertical representation should have a fitting error substantially smaller than the spatiotemporal prediction error.
