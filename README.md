# Argo Data Interpolation

Research code and working materials for interpolation and representation of Argo float CTD data across both vertical-profile and broader spatio-temporal settings.

The current implemented work centers on cycle-level vertical representation: fitting compact spline-based artifacts to individual Argo cycles so temperature and salinity can be queried at arbitrary pressures with uncertainty terms. The broader project direction extends beyond single-profile reconstruction toward spatio-temporal modeling across floats, where those cycle-level representations become inputs to larger interpolation and prediction workflows.

The long-term goal is to turn irregular Argo float measurements into compact, reusable representations that support larger-scale ocean reconstruction and climate analysis.

## At a Glance

- Implemented now: prototype cycle-level vertical representation code for individual Argo profiles under [`src/argo_interp/cycle`](src/argo_interp/cycle/).
- Documented now: literature reviews, topic notes, and notebook-based diagnostics indexed in [`research/README.md`](research/README.md).
- Planned next: broader spatio-temporal interpolation and prediction workflows across floats, with current research materials in [`research/spatio-temporal/README.md`](research/spatio-temporal/README.md).

## Research Entry Point

- [`research/README.md`](research/README.md): index of the project's research materials, methodology, and current research topics.

## Example

The library turns filtered Argo observations into cycle-level interpolation
models, then uses those cycle models as support for local spatio-temporal field
queries.

```python
from pathlib import Path
import pickle

from argo_interp.collection import CycleCollection
from argo_interp.cycle import ModelSettings
from argo_interp.cycle.adapter import PchipAdapter
from argo_interp.data import data_filter, get_data
from argo_interp.field import FieldQuery, LocalWeightedField

data_path = Path("data")
data_path.mkdir(exist_ok=True)

box = [
    80, 99,                    # longitude bounds
    6, 23,                     # latitude bounds
    0, 750,                    # pressure bounds
    "2016-01-01", "2018-12-31",
]

argo_data_path = data_path / "argo_data.pkl"
if argo_data_path.exists():
    with argo_data_path.open("rb") as f:
        ds = pickle.load(f)
else:
    ds = get_data(box, progress=True)
    with argo_data_path.open("wb") as f:
        pickle.dump(ds, f)

ds = data_filter(
    ds,
    [
        ds["PRES_QC"].isin([1, 2]),
        ds["TEMP_QC"].isin([1, 2]),
        ds["PSAL_QC"].isin([1, 2]),
    ],
)

settings = ModelSettings(n_folds=5)
cycles = CycleCollection.from_dataset(ds, PchipAdapter, settings)

field = LocalWeightedField(
    cycles,
    spatial_scale_km=500,
    spatial_radius_km=1000,
    temporal_scale_days=365 * 3,
    seasonal_scale_days=7 * 4,
    min_support=1,
)

pressure_grid = [50, 100, 200, 500]
field_model_error = field.cross_validate(pressure_grid, n_folds=5)
field = field.with_model_error(field_model_error)

queries = [
    FieldQuery(latitude, longitude, "2017-01-01", pressure_grid)
    for latitude in [7.0, 7.5, 8.0]
    for longitude in [80.5, 81.0]
]

profile = field.interpolate(queries)
profile.to_frame().sort_values(["query_index", "pressure"])
```

The returned `FieldProfile` includes interpolated temperature and salinity,
combined error estimates, separate cycle/field/model error components, support
counts, and support weights for each query-pressure record.

## Argo Background

- [How Argo floats work](https://youtu.be/YI_qhwMB9ME?si=kp0Rc3PNzKyzwS2l): a concise external explainer on Argo float operation and the observing system context behind this repository's data source.

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
Codex, and contains a mix of AI-generated and human-generated code and
documentation. AI may support code analysis, design comparison, implementation
review, research organization, and alignment between the implemented pipeline
and its documented research basis. Final authority for repository content rests
with the human developer. The way AI is used within the research documents
themselves is described in
[`research/research-methodology.md`](research/research-methodology.md).
Repository-specific AI agent policies are documented in [`AGENTS.md`](AGENTS.md).

## Acknowledgments

This work was inspired by participation in the 2025 MATE Floats workshop and
by the work of University of Washington Oceanography student Alnis Smidchens.

## License

This repository uses a split license:

- Project materials outside [`research/`](research/) are licensed under the GNU General Public License v3.0 or later. See [`LICENSE`](LICENSE).
- Everything under [`research/`](research/) is licensed under the Creative Commons Attribution 4.0 International license. See [`research/LICENSE`](research/LICENSE) and [`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt).

Bundled license texts remain under their own upstream terms. Path-based
project-content license assignments are recorded in [`REUSE.toml`](REUSE.toml).
