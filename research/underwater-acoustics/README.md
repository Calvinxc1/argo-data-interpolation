# Underwater Acoustics

This folder contains research materials on underwater acoustic use cases for uncertainty-aware Argo profile interpolation. The focus is on downstream sound-speed-profile workflows, replication targets for demonstration studies, and operational framing for acoustics-sensitive subsea applications.

This topic depends materially on the upstream vertical-method work in [../argo-cycle-representation/README.md](../argo-cycle-representation/README.md). The intent here is not to replace that work, but to identify a credible downstream demonstration where uncertainty-aware profile interpolation changes something operationally legible.

For this topic, [literature-review.md](literature-review.md) is the canonical literature-review artifact. The current review now synthesizes the broader topic literature around sound-speed equations, Argo-derived regional acoustics, interpolation methods, uncertainty, operational acoustics, machine learning, and Argo program expansion. Most of the bibliography has local full-text support, while unresolved items are tracked explicitly in [source-acquisition-tracker.md](source-acquisition-tracker.md).

## Research Files

- [literature-review.md](literature-review.md): canonical topic literature review, now centered on the methodological gap that profile-level interpolation choices are under-documented and weakly validated in Argo-to-sound-speed workflows.
- [source-acquisition-tracker.md](source-acquisition-tracker.md): tracker for the remaining unresolved bibliography items and acquisition blockers.
- [notes/README.md](notes/README.md): index of topic working notes, including the Jana replication rationale, project-framing implications, and broader operational framing.
- [notebooks/README.md](notebooks/README.md): index of the four-step notebook sequence from calibrated Jana replication through held-out baseline and weighted-extension validation.

## Current Maturity

- The Jana et al. Bay of Bengal replication and validation sequence is the most mature empirical part of this topic.
- The literature review is now a source-backed synthesis rather than a Jana-only draft, with the remaining unresolved sources tracked explicitly in the acquisition tracker.
- The notes and notebooks now tell a consistent progression: literature gap, replication baseline, comparative validation, weighted extensions, and operational translation.
- Operational framing, tooling gaps, and some downstream application claims still remain in working-note status until the corresponding primary sources are promoted into the canonical review.

## License

This folder is part of the [`research/`](../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../LICENSE`](../LICENSE). The
non-research parts of the repository remain under the GNU General Public
License v3.0 or later as described in [`../../README.md`](../../README.md).
