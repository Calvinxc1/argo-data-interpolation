# Research

This directory contains the project's working research materials: literature reviews, topic notes, notebooks, and shared methodology documents. The research process combines AI-assisted source discovery and organization with manual verification against original sources, with the goal of keeping the written research record aligned with both the cited literature and the implemented methods in the code.

The shared review and verification approach for these documents is described in [research-methodology.md](research-methodology.md).

## Current Research Topics

- [argo-cycle-representation](argo-cycle-representation/README.md): research on cycle-level vertical profile representation, interpolation, uncertainty modeling, and compression for individual Argo float profiles.
- [spatio-temporal](spatio-temporal/README.md): research on broader spatio-temporal Argo modeling, including functional-data and kriging-based approaches built on vertical profile representations.
- [underwater-acoustics](underwater-acoustics/README.md): research on downstream underwater-acoustics use cases, including sound-speed-profile workflows, the Jana et al. replication target, and operational framing for uncertainty-aware Argo interpolation.

## Standard Folder Structure

Each topic-specific research folder is intended to use the same core structure:

- `literature-review.md`: the canonical source-backed synthesis for that topic.
- `notes/`: optional folder for working notes, framing notes, implementation notes, operationalization notes, and other topic-specific working documents.
- `notebooks/`: optional folder for exploratory or prototype notebooks documenting concrete experiments, diagnostics, and method behavior.
- `sources/`: optional folder for local copies of papers, reports, manuals, and other reference materials.

When `notes/` exists, it should include a `README.md` that indexes the notes in that folder. When `notebooks/` exists, it should include a `README.md` that indexes the notebooks in that folder.

Source-backed claims in topic notes and notebooks should trace to sources already covered in that topic's `literature-review.md`. If a note or notebook needs a new source-backed claim, update the literature review first or in the same change.
