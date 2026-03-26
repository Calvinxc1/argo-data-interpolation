# Framing Notes: Argo Cycle Representation

These working notes capture project positioning, claim boundaries, and implementation-oriented framing for the current vertical representation work. Source-backed claims in this file should trace to [../literature-review.md](../literature-review.md). Candidate future sources are noted explicitly as pending literature-review inclusion rather than treated as established support.

## Project framing refinement

This project should not be framed as a new general Argo interpolation method or as an end-to-end acoustic range prediction solution.

The tighter working framing is:

**A compact, uncertainty-aware Argo-derived vertical profile or baseline prior for near-real-time acoustic range support and related operational oceanography workflows.**

This framing reflects a systems position rather than a claim of algorithmic dominance. The strongest use case is upstream support: a compact vertical representation that can provide an efficient environmental baseline or prior layer for mission-specific acoustic workflows and adjacent operational oceanography use cases.

### Candidate operational anchors to move into the literature review

Potential operational anchors for later source-backed treatment include public reporting around:

- Canadian Argo national reporting on real-time Argo profile use by DND scientists, operational oceanographers, and sonar operators, including Ocean Navigator-based workflows
- NOAA-facing descriptions of Argo support for acoustic propagation modeling through near-real-time temperature and salinity profiles

Until those sources are reviewed and added to the literature review, they should remain acquisition targets or framing cues rather than cited support in source-backed writing.

### What this implies for positioning

The strongest positioning is not "replace the acoustic model" or "win against gold-standard interpolation everywhere." The stronger and more defensible position is an enabling layer with the following properties:

- compact
- fast to compute and update
- queryable at arbitrary depths
- uncertainty-aware
- suitable for fusion with sparse onboard CTD or XCTD observations and/or model outputs

Good framing language to reuse:

- acoustic decision-support infrastructure
- baseline or prior layer for mission-specific ocean acoustic workflows
- compact uncertainty-aware vertical profile representation for real-time Argo-supported acoustic operations

### What to avoid claiming

- state-of-the-art acoustic prediction
- replacement for gold-standard ocean or acoustic modeling
- general best interpolation method

### What eventually has to be demonstrated

These are project requirements, not current validated results:

1. The representation is lighter or faster in a way that matters operationally.
2. The built-in uncertainty is actionable, not merely mathematically elegant.
3. The representation improves or simplifies baseline or prior generation for acoustic decision support, especially when local sensing is sparse or constrained.

### Working one-line pitch

**A compact, uncertainty-aware Argo profile encoding layer for near-real-time acoustic decision support, designed to provide efficient baseline ocean structure priors for mission-specific workflows.**

## Working framing for the current vertical method

The current implementation is best understood as a compact, queryable reconstruction artifact for a single Argo cycle rather than as an exact interpolant. That framing matters because several of its practical strengths come from deliberately not reproducing every observed point.

For the current pipeline, the most important working differentiators are:

- compact representation rather than retention of the raw observation grid
- tunability across accuracy and efficiency regimes
- depth-varying uncertainty terms rather than point estimates alone
- explicit error attribution across named uncertainty components
- robustness to noisy or outlying observations through smoothing plus LSQ fitting

This is an implementation-oriented interpretation of the method, not a claim established directly by the published literature.

### Accuracy-efficiency tradeoff

One useful way to describe the method is as occupying a different point on the tradeoff frontier than exact interpolants such as Akima, PCHIP, or MRST-PCHIP. The design target is not best possible offline reconstruction at any storage or compute cost. The design target is fit-for-purpose reconstruction with a much smaller stored artifact and simpler query-time behavior.

That tradeoff should be made explicit in any later write-up. If the method is less accurate than the strongest exact-interpolation baseline on some benchmark, that does not by itself invalidate the approach if the storage, robustness, and uncertainty behavior are materially better for the intended use.

### Confidence intervals and tunability

The method's uncertainty output is one of its more important distinctions relative to point-estimate-only baselines. A lower-fidelity, more compact operating mode is acceptable only if the intervals widen appropriately rather than hiding the loss in fidelity. This is currently a design expectation that should be checked explicitly in future tuning experiments.

### Error attribution

The intended uncertainty decomposition is meant to stay semantically legible. For the current vertical artifact, the relevant categories are:

- measurement uncertainty tied to the input sensors
- reconstruction uncertainty tied to the fitted representation
- support uncertainty only once the work expands beyond a single profile into a spatiotemporal layer
- source-data uncertainty when using provisional rather than delayed-mode upstream data

For the present vertical-only pipeline, the first two are implemented concerns and the latter two are forward-looking categories.

### Robustness interpretation

The combination of smoothing before knot detection and LSQ fitting rather than exact interpolation suggests better robustness to local spikes and outliers than exact interpolants. That conclusion is still an implementation-level expectation until the comparison experiments are run directly. The relevant validation path is the planned noise-injection and spike-injection benchmark work rather than verbal comparison alone.

## Evidence of the value of this work

### The Li et al. (2022) framing

Li et al. (2022) established that MRST-PCHIP is the most accurate vertical interpolation method currently available, recovering ocean heat content estimates 14% larger than those produced by linear interpolation over the 1956-2020 historical record. The absolute magnitude of that gap is 40 Zeta Joules, with a corresponding thermosteric sea level rise correction of 0.55 mm/yr.

Critically, the 14% figure is the gap between linear interpolation and MRST-PCHIP. It does not apply as a claim for this pipeline over MRST-PCHIP. Li et al. (2022) establishes vertical interpolation accuracy as a climate-relevant problem with quantified downstream consequences, which motivates getting profile representation right.

### The equivalence argument

If the planned cross-validation comparison demonstrates that this pipeline produces reconstruction RMSE equivalent to MRST-PCHIP on the same profiles, then the following claim would be defensible: this pipeline matches the physical fidelity of the current community standard for vertical interpolation, which Li et al. (2022) established as the accuracy ceiling of observationally based ocean heat content estimation.

### The additional value beyond equivalence

Equivalence in reconstruction accuracy combined with superiority in other dimensions is the complete argument. Compression: 40 to 100x reduction in storage per profile per variable, with no retained raw data required at query time. Noise robustness: LSQ fitting averages over observations rather than honoring each one exactly, unlike all interpolating methods. Uncertainty quantification: depth-varying, physically decomposed, queryable from the stored artifact alone. Standalone queryability: arbitrary pressure queries from stored coefficients only, no original profile needed.
