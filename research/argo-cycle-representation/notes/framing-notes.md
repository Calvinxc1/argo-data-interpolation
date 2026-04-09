# Framing Notes: Argo Cycle Representation

These working notes capture project positioning, claim boundaries, and implementation-oriented framing for the current vertical representation work. Source-backed claims in this file should trace to [../literature-review.md](../literature-review.md). This file is the canonical place for the topic's high-level pitch and claim boundaries; more concrete audience and product concepts belong in [operationalization-notes.md](operationalization-notes.md).

## Project framing refinement

This project should not be framed as a new general Argo interpolation method or as an end-to-end acoustic range prediction solution.

The tighter working framing is:

**A compact, uncertainty-aware Argo-derived vertical profile representation for downstream oceanographic workflows, with acoustics-sensitive use cases as one current target.**

This framing reflects a systems position rather than a claim of algorithmic dominance. The strongest general use case is upstream support: a compact vertical representation that can provide an efficient environmental baseline or prior layer for downstream workflows without claiming to replace full ocean or acoustic models.

### What this implies for positioning

The strongest positioning is not "replace the acoustic model" or "win against gold-standard interpolation everywhere." The stronger and more defensible position is an enabling layer with the following properties:

- compact
- fast to compute and update
- queryable at arbitrary depths
- uncertainty-aware
- suitable for fusion with sparse onboard CTD or XCTD observations and/or model outputs

Good framing language to reuse:

- environmental prior layer for downstream workflows
- compact uncertainty-aware vertical profile representation
- queryable profile artifact for operational oceanography or acoustics-adjacent use cases

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

**A compact, uncertainty-aware Argo profile encoding layer designed to provide efficient baseline ocean-structure priors for downstream workflows.**

## Working framing for the current vertical method

The current implementation is best understood as a compact, queryable reconstruction artifact for a single Argo cycle rather than as an exact interpolant. That framing matters because several of its practical strengths come from deliberately not reproducing every observed point.

For the current representation direction, the most important working differentiators are:

- compact representation rather than retention of the raw observation grid
- tunability across accuracy and efficiency regimes
- depth-varying uncertainty terms rather than point estimates alone
- explicit error attribution across named uncertainty components
- possible robustness to noisy or outlying observations through non-exact smoothing fits

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

The earlier curvature-adaptive LSQ prototype used smoothing before knot detection and least-squares fitting rather than exact interpolation. That design suggested better robustness to local spikes and outliers than exact interpolants, but the prototype should now be treated as a negative result unless validation demonstrates otherwise. The current validation path should compare the historical prototype, FITPACK smoothing splines, linear interpolation, and PCHIP directly through noise-injection, spike-injection, and holdout-reconstruction benchmarks rather than relying on verbal comparison alone. See [curvature-adaptive-spline-negative-result.md](curvature-adaptive-spline-negative-result.md).

## Evidence of the value of this work

### The Li et al. (2022) framing

The literature review already summarizes Li et al. (2022) and the quantified downstream sensitivity of climate estimates to interpolation choice. The project-facing point here is narrower: that result shows why vertical representation quality matters, but it does not transfer any quantitative advantage from MRST-PCHIP to the current pipeline.

### The equivalence argument

If the planned cross-validation comparison demonstrates that this pipeline produces reconstruction RMSE equivalent to MRST-PCHIP on the same profiles, then the following claim would be defensible: this pipeline matches the physical fidelity of the current community standard for vertical interpolation, which Li et al. (2022) established as the accuracy ceiling of observationally based ocean heat content estimation.

### The additional value beyond equivalence

Equivalence in reconstruction accuracy combined with superiority in other dimensions would be the complete argument. Compression, noise robustness, uncertainty quantification, and standalone queryability all need to be measured against exact-interpolant baselines rather than assumed from the original curvature-adaptive design. The negative-result framing matters here: if the curvature-adaptive LSQ prototype fails to justify its complexity, the same value argument can still be tested for FITPACK smoothing splines or another compact non-exact representation.
