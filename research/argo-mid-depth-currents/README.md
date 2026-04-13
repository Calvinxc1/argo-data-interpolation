# Argo Mid-Depth Currents

This folder contains research materials on the problem of predicting, estimating, and validating mid-depth ocean currents from Argo float data.

This topic depends materially on the broader modeling context in [../spatio-temporal/README.md](../spatio-temporal/README.md), but this folder is explicitly about current estimation itself: trajectory-derived velocity products, error structure, vertical extrapolation limits, and assimilation-oriented pathways.

The current folder is an early-stage research seed built from a planning summary. The literature review and tracker are intentionally explicit about what is source-backed, what is still pending verification, and what remains proposal-level framing.

This branch of research originated while considering whether current movement might need to be treated as a factor in spatio-temporal interpolation during the Jana extension work. The current folder records the resulting current-prediction question as its own topic rather than as a sub-note inside that earlier line of work.

## Research Files

- [literature-review.md](literature-review.md): seed literature review for Argo trajectory-based current products, mid-depth current error analysis, vertical reference-velocity framing, and current-prediction caveats.
- [source-acquisition-tracker.md](source-acquisition-tracker.md): topic-root tracker for references that still need local source acquisition or bibliographic completion.
- [notes/README.md](notes/README.md): index of working notes for current-prediction framing and related follow-up questions.

## License

This folder is part of the [`research/`](../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../LICENSE`](../LICENSE). The
non-research parts of the repository remain under the GNU General Public
License v3.0 or later as described in [`../../README.md`](../../README.md).
