# Underwater Acoustics

This folder contains research materials on underwater acoustic use cases for uncertainty-aware Argo profile interpolation. The focus is on downstream sound-speed-profile workflows, replication targets for demonstration studies, and operational framing for acoustics-sensitive subsea applications.

This topic depends materially on the upstream vertical-method work in [../argo-cycle-representation/README.md](../argo-cycle-representation/README.md). The intent here is not to replace that work, but to identify a credible downstream demonstration where uncertainty-aware profile interpolation changes something operationally legible.

For this topic, [literature-review.md](literature-review.md) is the canonical literature-review artifact. The current review now synthesizes the broader topic literature around sound-speed equations, Argo-derived regional acoustics, interpolation methods, uncertainty, operational acoustics, machine learning, and Argo program expansion. Most of the bibliography has local full-text support, while unresolved items are tracked explicitly in [source-acquisition-tracker.md](source-acquisition-tracker.md).

## Research Files

- [literature-review.md](literature-review.md): canonical topic literature review, now centered on the methodological gap that profile-level interpolation choices are under-documented and weakly validated in Argo-to-sound-speed workflows.
- [source-acquisition-tracker.md](source-acquisition-tracker.md): tracker for the remaining unresolved bibliography items and acquisition blockers.
- [notes/README.md](notes/README.md): index of topic working notes, including the Jana replication rationale, project-framing implications, and broader operational framing.
- [notebooks/README.md](notebooks/README.md): index of the five-step notebook sequence from calibrated Jana replication through held-out baseline, weighted-extension validation, and deterministic model-build handoff for later uncertainty work.

## Current Maturity

- The Jana et al. Bay of Bengal replication and validation sequence is the most mature empirical part of this topic.
- The literature review is now a source-backed synthesis rather than a Jana-only draft, with the remaining unresolved sources tracked explicitly in the acquisition tracker.
- The notes and notebooks now tell a consistent progression: literature gap, replication baseline, comparative validation, weighted extensions, deterministic model build, and operational translation.
- Operational framing, tooling gaps, and some downstream application claims still remain in working-note status until the corresponding primary sources are promoted into the canonical review.

## Restructuring Note

This folder likely needs to be split more effectively as the broader research program matures. The current `underwater-acoustics` topic is carrying three related but distinct layers of work:

1. a downstream acoustics anchor, centered on why Argo-derived sound-speed structure matters operationally
2. a Jana et al.-based replication and benchmark sequence that makes that downstream case concrete
3. an expanding spatiotemporal interpolation line that grows back toward the original project goal and is not purely acoustics-specific

The project logic discussed across the current notes is:

1. `argo-cycle-representation` started as the foundational cycle-level interpolation problem
2. `underwater-acoustics` was developed as the first strong downstream anchor for that work, using Argo-based sound-speed estimation to make the interpolation problem operationally legible
3. once that anchor was established, the work naturally expanded back toward the original broader objective: spatiotemporal interpolation built on the same cycle-level foundation

That suggests a cleaner long-term branch structure:

1. `argo-cycle-representation`: foundational cycle/profile interpolation questions
2. `underwater-acoustics`: downstream acoustics case study and application framing
3. a future spatiotemporal-interpolation topic: local weighted prediction, support diagnostics, uncertainty-aware model building, and related general method work

If that split is carried out later, the likely first-pass allocation is:

- keep `literature-review.md`, `source-acquisition-tracker.md`, operational notes, the Jana replication note, and notebooks `1-4` in `underwater-acoustics`
- move notebook `5` and later general spatiotemporal model-build work into a separate topic once those artifacts are no longer primarily acoustics-facing
- keep the foundational interpolation argument and cycle-level method framing in `argo-cycle-representation`

This note is here to preserve the current intent: the apparent scope overlap is not random drift, but the result of a research path that moved from cycle-level foundations, to an acoustics anchor, and then back outward into the broader spatiotemporal interpolation program.

## License

This folder is part of the [`research/`](../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../LICENSE`](../LICENSE). The
non-research parts of the repository remain under the GNU General Public
License v3.0 or later as described in [`../../README.md`](../../README.md).
