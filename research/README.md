# Research

This directory contains the project's working research materials: literature reviews, research notes, notebooks, and shared methodology documents. The research process combines AI-assisted source discovery and organization with manual verification against original sources, with the goal of keeping the written research record aligned with both the cited literature and the implemented methods in the code.

The shared review and verification approach for these documents is described in [research-methodology.md](research-methodology.md).

## Current Research Topics

- [argo-cycle-representation](argo-cycle-representation/README.md): research on cycle-level vertical profile representation, interpolation, uncertainty modeling, and compression for individual Argo float profiles.
- [spatio-temporal](spatio-temporal/README.md): research on broader spatio-temporal Argo modeling, including functional-data and kriging-based approaches built on vertical profile representations.

## Standard Folder Structure

Each topic-specific research folder is intended to use the same core structure:

- `literature-review.md`: source-backed synthesis of the relevant literature for that topic.
- `research-notes.md`: working notes connecting the literature to the current implementation, hypotheses, and planned follow-up work.
- `research-notebook.ipynb`: exploratory or prototype notebook documenting concrete experiments, diagnostics, and method behavior for that topic when applicable.

Some topics may also carry additional notes when they serve a distinct purpose that does not fit the standard literature-review / research-notes / notebook split. Those files should stay outside `sources/` and should be described clearly in the topic `README.md`.

Not every research topic will necessarily use all three artifacts, but this is the intended baseline structure.
