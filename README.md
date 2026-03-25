# Argo Data Interpolation

Research code and working materials for interpolation and representation of Argo float CTD data across both vertical-profile and broader spatio-temporal settings.

The current implemented work centers on cycle-level vertical representation: fitting compact spline-based artifacts to individual Argo cycles so temperature and salinity can be queried at arbitrary pressures with uncertainty terms. The broader project direction extends beyond single-profile reconstruction toward spatio-temporal modeling across floats, where those cycle-level representations become inputs to larger interpolation and prediction workflows.

The long-term goal is to turn irregular Argo float measurements into compact, reusable representations that support larger-scale ocean reconstruction and climate analysis.

## At a Glance

- Implemented now: prototype cycle-level vertical representation code for individual Argo profiles under [`src/argo_interp/cycle`](src/argo_interp/cycle/).
- Documented now: literature reviews, research notes, and notebook-based diagnostics indexed in [`research/README.md`](research/README.md).
- Planned next: broader spatio-temporal interpolation and prediction workflows across floats, with current research materials in [`research/spatio-temporal/README.md`](research/spatio-temporal/README.md).

## Research Entry Point

- [`research/README.md`](research/README.md): index of the project's research materials, methodology, and current research topics.

## Project Status

This project is in exploratory/research mode.

- Vertical cycle-representation pipeline:
  implemented in code under [`src/argo_interp/cycle`](src/argo_interp/cycle/) and actively explored through the research notebook and supporting research documents.
- Spatio-temporal work:
  currently in research/planning mode, with literature review and working notes in place but no production-quality implementation yet.
- Validation and benchmarking:
  partial and prototype-level only. The current notebook demonstrates proof-of-concept diagnostics, but broad comparative benchmarking, regional validation, and failure-mode analysis remain unfinished.
- Packaging, CI, and productionization:
  not yet a project focus. Formal test suites, CI/CD workflows, and deployment-oriented setup are intentionally minimal at this stage.

## Roadmap

The current scope is vertical interpolation within individual float cycles
(depth-profile modeling). The next major milestone is extending this work to
**spatiotemporal interpolation across floats/buoys**, so predictions can use
both depth structure and cross-buoy spatial/temporal context.

Additional planned work includes examining temperature-salinity correlation
structure within cycles to evaluate whether joint modeling can improve
interpolation accuracy.

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

Released under the terms of the GNU Affero General Public License v3.0.
See [`LICENSE`](LICENSE).
