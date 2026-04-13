# Research

This directory contains the project's working research materials: literature reviews, topic notes, notebooks, and shared methodology documents. The research process combines AI-assisted source discovery and organization with manual verification against original sources, with the goal of keeping the written research record aligned with both the cited literature and the implemented methods in the code.

The shared review and verification approach for these documents is described in [research-methodology.md](research-methodology.md).

## Current Research Topics

- [argo-cycle-representation](argo-cycle-representation/README.md): research on cycle-level vertical profile representation, interpolation, uncertainty modeling, and compression for individual Argo float profiles.
- [argo-mid-depth-currents](argo-mid-depth-currents/README.md): research on Argo-derived mid-depth current products and on whether they could support current-aware interpolation.
- [spatio-temporal](spatio-temporal/README.md): research on broader spatio-temporal Argo modeling, including functional-data and kriging-based approaches built on vertical profile representations.
- [underwater-acoustics](underwater-acoustics/README.md): research on downstream underwater-acoustics use cases, including sound-speed-profile workflows, the Jana et al. replication target, and operational framing for uncertainty-aware Argo interpolation.

## Standard Folder Structure

Each topic-specific research folder is intended to use the same core structure:

- `literature-review.md`: the canonical source-backed synthesis for that topic.
- `source-acquisition-tracker.md`: optional topic-root tracker for unresolved local-source acquisition, verification caveats, and full-text follow-up.
- `notes/`: optional folder for working notes, framing notes, implementation notes, operationalization notes, and other topic-specific working documents.
- `notebooks/`: optional folder for exploratory or prototype notebooks documenting concrete experiments, diagnostics, and method behavior.
- `notebooks/lib/`: optional notebook-support code for research-only helpers such as benchmark runners, plotting utilities, or reproducible negative-result implementations that should not live under `src/`.
- `notebooks/data/`: optional local notebook artifact storage for cached intermediate data or other speed-oriented local artifacts that support notebook reruns but are not part of the canonical research record.
- `sources/`: optional folder for local copies of papers, reports, manuals, and other reference materials. When a local full-text source is non-English, include an accompanying same-stem Markdown file with the best available translation or translation notes.

When `notes/` exists, it should include a `README.md` that indexes the notes in that folder. When `notebooks/` exists, it should include a `README.md` that indexes the notebooks in that folder.
When `notebooks/lib/` exists, its purpose should be described from `notebooks/README.md` so the boundary between notebook narrative and research-only support code stays explicit.
When `notebooks/data/` exists, treat it as local process support rather than a canonical output location; durable findings should still be represented in tracked notebooks, notes, or other research documents.

Source-backed claims in topic notes and notebooks should trace to sources already covered in that topic's `literature-review.md`. If a note or notebook needs a new source-backed claim, update the literature review first or in the same change.

## License

Unless otherwise noted, materials in this directory are licensed under
the Creative Commons Attribution 4.0 International license. See
[`LICENSE`](LICENSE) and [`../LICENSES/CC-BY-4.0.txt`](../LICENSES/CC-BY-4.0.txt).
