# Adaptive Spline Analogues

This note records the project-facing relevance of the adaptive spline papers already summarized in [../literature-review.md](../literature-review.md). The literature review carries the source-backed paper summaries; this note keeps only the local interpretation of why those papers matter for the current Argo cycle representation work.

## Li et al. (2005): analogue for adaptive LSQ profile fitting

The local takeaway from Li et al. (2005) is that noise separation, adaptive knot placement, and least-squares fitting can form a coherent package rather than three unrelated choices. For this project, the paper is useful as a cross-domain analogue for treating knot allocation as a structural modeling decision rather than a fixed preprocessing choice.

## Vitenti et al. (2025): tolerance-driven refinement as an alternative design axis

The useful project-level idea from Vitenti et al. (2025) is not the specific astrophysical implementation but the design principle that knot allocation can be driven by an explicit precision target. That is relevant here as a possible alternative to curvature-driven allocation when the project eventually explores user-tunable accuracy regimes.

## Thielmann et al. (2025): knot placement and smoothing should not be treated as independent by default

The relevant takeaway from Thielmann et al. (2025) is methodological caution. If knot placement and smoothing interact strongly, then treating them as separable tuning decisions may leave performance on the table. That does not establish a required design for this project, but it does justify keeping joint optimization in view as the method matures.
