# Argo Cycle Representation Notes

This folder contains the working notes for the `argo-cycle-representation` topic. The notes are organized by purpose so framing, method comparison, uncertainty, experiments, and operationalization can evolve independently. The canonical source-backed entry point for the topic is [../literature-review.md](../literature-review.md).

For a quick pass through the topic, read the literature review first, then framing, method comparison, uncertainty, pipeline integration, operationalization, and experiment design. The adaptive-spline analogue note is best read after the lit review section on additional adaptive spline methods.

The notes should now be read with the notebook sequence in mind:

1. notebook 01 confirms the custom curvature-adaptive method is a real prototype rather than a dead idea on paper,
2. notebook 02 shows that prototype trading RMSE for compactness and footprint stability,
3. notebook 03 then shifts the active research direction toward simpler native spline-family methods and uncertainty-aware profile representation.

The curvature-adaptive negative-result note therefore records an important project branch, but it should be treated as method-development history rather than as the current default path.

## Files

- [framing-notes.md](framing-notes.md): project positioning, claim boundaries, and high-level value framing for the vertical representation work.
- [adaptive-spline-analogues.md](adaptive-spline-analogues.md): project-facing interpretation of the cross-domain spline and knot-allocation papers summarized in the lit review.
- [curvature-adaptive-spline-negative-result.md](curvature-adaptive-spline-negative-result.md): notes on preserving the curvature-adaptive LSQ spline as a negative-result branch and project-history element rather than the current default path.
- [method-comparison-notes.md](method-comparison-notes.md): working comparisons across exact interpolants, the custom adaptive prototype, and the simpler spline-family alternatives that now matter most.
- [pipeline-integration-notes.md](pipeline-integration-notes.md): notes on where the vertical artifact fits into the broader Argo processing and downstream analysis chain.
- [experiment-design-notes.md](experiment-design-notes.md): implementation notes plus the remaining experiments that still matter after the completed notebook comparisons.
- [uncertainty-notes.md](uncertainty-notes.md): uncertainty decomposition, sensor-error conventions, and how the uncertainty story changes between the historical custom prototype and the current spline-family direction.
- [operationalization-notes.md](operationalization-notes.md): product-facing and audience-facing framing for acoustic decision support and related operational workflows.

## License

This folder is part of the [`research/`](../../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../../LICENSE`](../../LICENSE).
The non-research parts of the repository remain under the GNU General
Public License v3.0 or later as described in
[`../../../README.md`](../../../README.md).
