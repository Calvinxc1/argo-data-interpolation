# Changelog

All notable user-visible, operator-visible, and release-relevant changes in this repository are recorded here.

## Staged

Changes merged to `dev` and staged for a future release belong in this section until they are promoted into a versioned release entry.

_No staged changes._

## 0.1.0 - 2026-08-23

### Added

- Added `scipy-stubs` to the development dependency set to improve local type-checking support for SciPy usage during development.
- Added a first pytest-based unit-test harness, PR-only test workflow, coverage reporting, and PR-visible test summaries for pull requests to `dev` and `main`.
- Added automatic Ruff linting with PR-only reporting and PR-visible lint summaries alongside the test workflow.
- Added a Bay of Bengal Jana et al. replication notebook under the underwater-acoustics research topic, along with companion notes documenting the settled replication pipeline, validation outputs, and subdomain figure workflow.
- Added `cartopy` and `seawater` as runtime dependencies to support the research notebook mapping and UNESCO sound-speed replication workflow.
- Added the reusable `argo_interp.uncertainty` API for the Notebook 6 TEOS-10 sound-speed uncertainty product, including explicit configuration, spatial-variance estimation, geometry selection, provenance metadata, and batched grid construction.
- Added `PRODUCT_COLUMN_DTYPES` and `empty_product_frame()` to `argo_interp.uncertainty`, giving sound-speed product tables a single declared dtype schema that row-less results also carry.

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
- Moved Notebook 6's reusable uncertainty-product computation onto `argo_interp.uncertainty`, retaining its validated planar-degree configuration. The historical `depth_m` field remains a pressure-grid label equal to `pressure_dbar`; physical-depth conversion is deferred future work.
- Moved Argopy/Xarray data access and notebook-only packages into explicit `data` and `research` extras, keeping the installed core focused on the public modeling and uncertainty APIs.
- Updated package license metadata to the SPDX form required by current Python packaging tooling.
- Streamlined the paired Notebook 6 research artifact by moving cache/model rebuild, benchmarking, and plotting mechanics into topic-local support modules; removed unused direct Argopy imports from the earlier cycle-representation notebooks.
- Clarified that PyPI distribution is forthcoming and that the repository checkout remains the current installation path.
- Renamed the distributed package from `argo-data-interpolation` to `argo-interp`. The optional extras are now installed as `argo-interp[data]` and `argo-interp[research]`, and the import-error message raised by `argo_interp.data.get_data` names the new package.
- Rebuilt `CycleModels.interp_error_variance()` on preallocated arrays instead of column-by-column DataFrame assignment, matching the interpolation path and removing per-cycle frame fragmentation on large bundles.

### Fixed

- Fixed `SplineAdapter.fit` to apply `extrapolate` on the fitted `BSpline` object instead of passing it to `make_splrep`, preventing runtime `TypeError` and restoring configurable extrapolation behavior.
- Fixed `Model.interpolate()` and `Model.interp_error()` to normalize scalar pressure inputs consistently, including integer scalars, while cleaning the remaining Ruff line-length violations in the runtime and test code.
- Constrained Erddapy below 3.3 because Argopy 1.4.0 imports a symbol removed by Erddapy 3.3, which otherwise prevents Argo data fetching from importing.
- Made the CI pytest step preserve test failures when its output is captured for PR summaries.
- Preserved uncertainty provenance on frames yielded by `SoundSpeedUncertaintyProduct.iter_grid_batches()`.
- Made weighted profile means exclude all non-finite input values, consistent with their finite-support contract.
- Fixed `ModelSettings` sharing one default `ModelKwargs` instance across every default-constructed settings object, so mutating adapter kwargs on one settings object no longer leaks into all others in the same process.
- Fixed sound-speed product queries that match no candidate cycles returning an all-object-dtype frame, which did not match the dtypes of a populated result.
- Fixed `SoundSpeedUncertaintyProduct` serving stale position-indexed cycle terms after its `CycleModels` bundle was mutated, which silently misaligned cached values against live metadata.

### Removed

- Removed unused runtime dependencies `pydantic` and `ruptures`.
- Removed the older root-level Jana replication notebook copy and the now-obsolete `data_qc_pass` helper in favor of the reorganized research notebook and generalized filter utility.

### Security

- None.
