# Argo Cycle Representation

This folder contains research materials on compact vertical representation of individual Argo float cycles. The focus is on replacing raw per-cycle profile observations with a queryable spline-based artifact that preserves large-scale vertical structure, supports uncertainty estimates, and can serve as input to downstream spatio-temporal modeling. The work here examines vertical interpolation and representation methods relevant to Argo profiles, with particular attention to adaptive knot placement, noise-robust spline fitting, Argo QC uncertainty conventions, and the trade-off between compact representation and exact interpolation.

For this topic, [literature-review.md](literature-review.md) is the canonical source-backed document. Source-backed claims in the notes and notebooks for this folder should trace to sources already covered there.

## Research Files

- [literature-review.md](literature-review.md): source-backed review of interpolation methods, adaptive splines, and Argo QC/error context.
- [notes/README.md](notes/README.md): index of topic working notes, including framing, method comparison, uncertainty, experiments, and operationalization.
- [notebooks/README.md](notebooks/README.md): index of prototype notebook artifacts for the current spline workflow, comparative validation against exact interpolants, uncertainty, and diagnostics.
