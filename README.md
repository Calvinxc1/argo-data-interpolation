# argo-kwsi

Research code and working materials for interpolation and representation of Argo float CTD data across both vertical-profile and broader spatio-temporal settings.

The current implemented work centers on cycle-level vertical representation: fitting compact spline-based artifacts to individual Argo cycles so temperature and salinity can be queried at arbitrary pressures with uncertainty terms. The broader project direction extends beyond single-profile reconstruction toward spatio-temporal modeling across floats, where those cycle-level representations become inputs to larger interpolation and prediction workflows.

The long-term goal is to turn irregular Argo float measurements into compact, reusable representations that support larger-scale ocean reconstruction and climate analysis.

## At a Glance

- Implemented now: cycle-level vertical representation code under [`src/argo_kwsi/cycle`](src/argo_kwsi/cycle/) and a reusable spatiotemporal TEOS-10 uncertainty-product API in [`argo_kwsi.uncertainty`](src/argo_kwsi/uncertainty.py).
- Documented now: literature reviews, topic notes, and notebook-based diagnostics indexed in [`research/README.md`](research/README.md).
- Planned next: broader spatio-temporal interpolation and prediction workflows across floats, with current research materials in [`research/spatio-temporal/README.md`](research/spatio-temporal/README.md).

## Research Entry Point

- [`research/README.md`](research/README.md): index of the project's research materials, methodology, and current research topics.

## Installation

PyPI distribution is forthcoming. Until it is published, install and run the
package from a source checkout. The planned distribution will provide a small
core package plus `data` and `research` extras for Argo access and
research-specific analysis dependencies.

For the complete notebook environment when working from this repository, run:

```bash
uv sync --all-groups
```

## Release Process

Releases are driven by the `version` field in `pyproject.toml`, not by a
hand-made tag. Merging a release branch into `main` is the release event: the
[Release workflow](.github/workflows/release.yml) reads that version, stops if
it is already tagged, and otherwise re-runs lint, tests and the REUSE check,
builds an sdist and a wheel, smoke-tests the wheel in isolation, publishes to
PyPI, then tags the commit and drafts a GitHub release from this version's
`CHANGELOG.md` section.

Publishing runs before tagging, so a version is never tagged unless it actually
reached PyPI. If a run fails between the two, re-run the workflow manually from
the Actions tab; the publish step skips files PyPI already has.

Two settings must exist outside the repository before the first release:

- A [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/) for this
  repository, with workflow `release.yml` and environment `pypi`. For a project
  not yet on PyPI, create it as a *pending* publisher.
- A GitHub Actions environment named `pypi`, matching the publisher entry.

## Paper Boundary

This repository is the source of truth for the code, supporting research
materials, reproducibility work, and visualizations that feed downstream
writing. The OCEANS 2026 Monterey paper is a separate downstream artifact
maintained outside this repository under Education ownership. Paper drafts and
bibliography should point back here for implementation, methodology support,
and figures rather than duplicating repository-owned source material.

Three figures generated here appear as Fig. 1 of that paper, whose published
form is © 2026 IEEE. The repository copies are the author's own originals
under the `research/` CC-BY-4.0 license rather than reproductions of the
published article; see
[`research/underwater-acoustics/notes/paper-figure-provenance.md`](research/underwater-acoustics/notes/paper-figure-provenance.md).

## Argo Background

- [How Argo floats work](https://youtu.be/YI_qhwMB9ME?si=kp0Rc3PNzKyzwS2l): a concise external explainer on Argo float operation and the observing system context behind this repository's data source.

## Project Status

This project is in exploratory/research mode.

- Vertical cycle-representation pipeline:
  implemented in code under [`src/argo_kwsi/cycle`](src/argo_kwsi/cycle/) and actively explored through the research notebook and supporting research documents.
- Spatio-temporal work:
  the Notebook 6 TEOS-10 uncertainty-product computation is available as a library API; data acquisition, cached reproducibility artifacts, plotting, and broader validation remain research workflows.
- Validation and benchmarking:
  partial and prototype-level only. The current notebook demonstrates proof-of-concept diagnostics, but broad comparative benchmarking, regional validation, and failure-mode analysis remain unfinished.
- Packaging and CI:
  the package has unit tests on Python 3.11 and 3.13, coverage enforcement,
  linting, REUSE licensing compliance, a wheel-install smoke test, and an
  automated release pipeline that tags, publishes to PyPI, and drafts release
  notes. Broader production hardening remains future work.

## Roadmap

The current scope is vertical interpolation within individual float cycles
(depth-profile modeling). The next major milestone is extending this work to
**spatiotemporal interpolation across floats/buoys**, so predictions can use
both depth structure and cross-buoy spatial/temporal context.

Additional planned work includes examining temperature-salinity correlation
structure within cycles to evaluate whether joint modeling can improve
interpolation accuracy.

## Sound-Speed Uncertainty API

`argo_kwsi.uncertainty` packages the computational core of the underwater
acoustics Notebook 6 product. Create one explicit configuration and reuse it
to estimate depthwise spatial variance and build query-point or gridded
TEOS-10 sound-speed estimates with componentized uncertainty:

```python
from argo_kwsi.uncertainty import (
    SoundSpeedUncertaintyConfig,
    SoundSpeedUncertaintyProduct,
    estimate_depthwise_spatial_variance,
)

config = SoundSpeedUncertaintyConfig.notebook6()
spatial_variance = estimate_depthwise_spatial_variance(cycle_models, config)
product = SoundSpeedUncertaintyProduct(
    cycle_models=cycle_models,
    spatial_variance=spatial_variance,
    config=config,
)
query_table = product.query(latitude=15.0, longitude=88.0)
grid_table = product.grid(latitudes, longitudes)
```

`SoundSpeedUncertaintyConfig.notebook6()` preserves the Notebook 6 setting:
a local rectangular prefilter and Euclidean distance in latitude/longitude
degrees. For global work, set `distance_metric="great_circle_km"` and express
both the candidate radius and distance-kernel sigma in kilometres.

The result tables include provenance in
`DataFrame.attrs["argo_kwsi_uncertainty"]`; use `query_result()` or
`grid_result()` when you need the table and metadata as separate fields. Use
`iter_grid_batches(...)` rather than `grid(...)` for a large grid that should
be persisted in chunks.

The package currently uses the validated independent-temperature/salinity
delta-method simplification: it excludes T-S covariance and TEOS-10 formula
uncertainty. `depth_m` presently mirrors `pressure_dbar`; physical-depth
conversion is explicitly deferred future work and should not be inferred from
that column.

## AI Assistance

This repository uses AI-assisted development workflows, including Claude and
Codex. In code work, AI may use the repository's research materials to support
code analysis, design comparison, implementation review, and alignment between
the implemented pipeline and its documented research basis. The way AI is used
within the research documents themselves is described in
[`research/research-methodology.md`](research/research-methodology.md). All
AI-assisted work is reviewed by a human before publication. In general, core
implementation code is not delegated to AI, though AI may still be used to
brainstorm approaches, compare design options, and support surrounding analysis
and documentation work. Repository-specific AI agent policies are documented in
[`AGENTS.md`](AGENTS.md).

## Acknowledgments

This work was inspired by participation in the 2025 MATE Floats workshop and
by the work of University of Washington Oceanography student Alnis Smidchens.

## License

This repository uses a split license:

- Project materials outside [`research/`](research/) are licensed under the GNU General Public License v3.0 or later. See [`LICENSE`](LICENSE).
- Everything under [`research/`](research/) is licensed under the Creative Commons Attribution 4.0 International license. See [`research/LICENSE`](research/LICENSE) and [`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt).

Bundled license texts remain under their own upstream terms. Path-based
project-content license assignments are recorded in [`REUSE.toml`](REUSE.toml).
