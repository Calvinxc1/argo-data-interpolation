# Argo Cycle Representation

This folder contains research materials on compact vertical representation of individual Argo float cycles. The central research question is how to represent a single Argo profile as a compact, queryable artifact with useful uncertainty information, without collapsing the problem into pure exact interpolation.

The topic currently reads as a staged exploration:

1. a custom curvature-adaptive least-squares spline was developed as an initial compact-representation prototype,
2. that prototype was validated internally and then compared against exact-interpolant baselines,
3. the comparison was then widened to simpler native spline-family alternatives, which now define the more durable research direction.

So the folder is not only about one spline implementation. It is about the broader representation problem, the custom adaptive prototype as a serious exploratory branch, and the eventual shift toward simpler spline-family methods plus uncertainty-aware profile encoding.

For this topic, [literature-review.md](literature-review.md) is the canonical source-backed document. Source-backed claims in the notes and notebooks for this folder should trace to sources already covered there.

## Research Files

- [literature-review.md](literature-review.md): source-backed review of interpolation methods, adaptive splines, and Argo QC/error context.
- [source-acquisition-tracker.md](source-acquisition-tracker.md): topic-root tracker for local-source verification caveats and any remaining acquisition exceptions.
- [notes/README.md](notes/README.md): index of topic working notes, including framing, method comparison, uncertainty, experiments, and operationalization.
- [notebooks/README.md](notebooks/README.md): index of the staged notebook sequence: confirm the custom method, compare it to exact interpolants, then test whether simpler native spline methods supersede it.

## License

This folder is part of the [`research/`](../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../LICENSE`](../LICENSE). The
non-research parts of the repository remain under the GNU General Public
License v3.0 or later as described in [`../../README.md`](../../README.md).
