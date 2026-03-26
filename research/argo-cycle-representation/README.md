# Argo Cycle Representation

This folder contains research materials on compact vertical representation of individual Argo float cycles. The focus is on replacing raw per-cycle profile observations with a queryable spline-based artifact that preserves large-scale vertical structure, supports uncertainty estimates, and can serve as input to downstream spatio-temporal modeling. The work here examines vertical interpolation and representation methods relevant to Argo profiles, with particular attention to adaptive knot placement, noise-robust spline fitting, Argo QC uncertainty conventions, and the trade-off between compact representation and exact interpolation.

## Research Files

- [literature-review.md](literature-review.md): source-backed review of interpolation methods, adaptive splines, and Argo QC/error context.
- [research-notes.md](research-notes.md): working notes on pipeline implications, hypotheses, and next experiments.
- [operationalization-notes.md](operationalization-notes.md): product-facing and audience-facing framing notes for operational use cases and acoustics-oriented positioning.
- [research-notebook.ipynb](research-notebook.ipynb): prototype notebook for the current spline workflow, uncertainty, and diagnostics.
