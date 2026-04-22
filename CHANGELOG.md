# Changelog

All notable user-visible, operator-visible, and release-relevant changes in this repository are recorded here.

## Staged

Changes merged to `dev` and staged for a future release belong in this section until they are promoted into a versioned release entry.

### Added

- Added `scipy-stubs` to the development dependency set to improve local type-checking support for SciPy usage during development.
- Added a first pytest-based unit-test harness, PR-only test workflow, coverage reporting, and PR-visible test summaries for pull requests to `dev` and `main`.
- Added automatic Ruff linting with PR-only reporting and PR-visible lint summaries alongside the test workflow.
- Added a Bay of Bengal Jana et al. replication notebook under the underwater-acoustics research topic, along with companion notes documenting the settled replication pipeline, validation outputs, and subdomain figure workflow.
- Added `cartopy` and `seawater` as runtime dependencies to support the research notebook mapping and UNESCO sound-speed replication workflow.

### Changed

- Added a changelog workflow policy and established this file as the single source of truth for staged and released change history.
- Documented repository execution policy that authenticated `gh` commands must run outside the sandbox because sandboxed sessions cannot access the local keyring-backed GitHub CLI credentials.
- Added a repository notebook workflow rule requiring Jupytext `.py` files to be resynced from diverged `.ipynb` notebooks before notebook-source edits, and requiring explicit user direction before syncing edits back into notebooks.
- Optimized the underwater-acoustics uncertainty model-build notebook hold-one-out validation loop by replacing repeated `CycleModels.filter()/pop()` usage with direct metadata masking and shared vectorized weighting while preserving the full temperature and salinity error matrices.
- Split repository licensing so `research/` materials are documented and machine-mapped as `CC-BY-4.0` while non-research project materials remain `GPL-3.0-or-later`.
- Refactored topic-level research organization to support indexed `notes/` and `notebooks/` directories while keeping `literature-review.md` as the canonical source-backed artifact for each topic.
- Standardized `source-acquisition-tracker.md` as a topic-root research artifact and added policy requiring same-stem Markdown translation companions for non-English local full-text sources.
- Reorganized the Argo cycle-representation research materials into focused note files, moved notebook artifacts under an indexed notebooks folder, and aligned the spatio-temporal topic with the same notes-based layout.
- Added research-policy rules requiring topic notes and notebooks to trace source-backed claims back through the topic literature review and to keep working-note structure consistent with the new folder model.
- Updated research-source policy so books can resolve through repo-local Markdown source notes when PDFs cannot practically be stored, and aligned the underwater-acoustics literature review and acquisition tracker with that workflow.
- Reduced `CycleModel` memory and serialization overhead substantially by replacing heavy metadata models with slotted dataclasses and using compact custom pickle state.
- Split notebook and research dependencies into a dedicated `research` dependency group while keeping the core runtime dependency surface limited to `numpy`, `pandas`, and `scipy`.
- Reworked cycle-model settings so validation and interpolation can use distinct temperature and salinity kwargs through a dedicated settings package and shared sensor-accuracy configuration.
- Replaced the Argo QC helper with a more general `data_filter` utility, exposed that helper from `argo_interp.data`, and updated the research fetch path to accept an explicit `mode` plus larger default time chunks.
- Split shared cycle classes into explicit `argo_interp.cycle.domain` and `argo_interp.cycle.config` public packages, removed duplicate legacy type modules under `cycle/model`, and updated model/validation wiring plus the Jana replication notebook to use the new API surface.

### Fixed

- Fixed `SplineAdapter.fit` to apply `extrapolate` on the fitted `BSpline` object instead of passing it to `make_splrep`, preventing runtime `TypeError` and restoring configurable extrapolation behavior.
- Fixed `Model.interpolate()` and `Model.interp_error()` to normalize scalar pressure inputs consistently, including integer scalars, while cleaning the remaining Ruff line-length violations in the runtime and test code.

### Removed

- Removed unused runtime dependencies `pydantic` and `ruptures`.
- Removed the older root-level Jana replication notebook copy and the now-obsolete `data_qc_pass` helper in favor of the reorganized research notebook and generalized filter utility.

### Security

- None yet.
