# Changelog

All notable user-visible, operator-visible, and release-relevant changes in this repository are recorded here.

## Staged

Changes merged to `dev` and staged for a future release belong in this section until they are promoted into a versioned release entry.

### Added

- Added `scipy-stubs` to the development dependency set to improve local type-checking support for SciPy usage during development.
- Added a first pytest-based unit-test harness, PR-only test workflow, coverage reporting, and PR-visible test summaries for pull requests to `dev` and `main`.
- Added automatic Ruff linting with PR-only reporting and PR-visible lint summaries alongside the test workflow.

### Changed

- Added a changelog workflow policy and established this file as the single source of truth for staged and released change history.
- Refactored topic-level research organization to support indexed `notes/` and `notebooks/` directories while keeping `literature-review.md` as the canonical source-backed artifact for each topic.
- Reorganized the Argo cycle-representation research materials into focused note files, moved notebook artifacts under an indexed notebooks folder, and aligned the spatio-temporal topic with the same notes-based layout.
- Added research-policy rules requiring topic notes and notebooks to trace source-backed claims back through the topic literature review and to keep working-note structure consistent with the new folder model.
- Reduced `CycleModel` memory and serialization overhead substantially by replacing heavy metadata models with slotted dataclasses and using compact custom pickle state.
- Split notebook and research dependencies into a dedicated `research` dependency group while keeping the core runtime dependency surface limited to `numpy`, `pandas`, and `scipy`.
- Reworked cycle-model settings so validation and interpolation can use distinct temperature and salinity kwargs through a dedicated settings package and shared sensor-accuracy configuration.

### Fixed

- None yet.

### Removed

- Removed unused runtime dependencies `pydantic` and `ruptures`.

### Security

- None yet.
