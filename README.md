# Argo Data Interpolation

Interpolation tools for Argo float CTD profiles (pressure, temperature, salinity).

This repository currently focuses on **cycle-level vertical interpolation**:
given observations from a single Argo cycle, fit spline models that can return
temperature and salinity at arbitrary pressure values, with uncertainty terms.

## Project Status

This project is in exploratory/research mode.

- Core cycle interpolation pipeline is implemented under `src/argo_interp/cycle`.
- Notebook-driven experimentation is in `playground.ipynb`.
- CI/CD and formal test suites are intentionally not set up yet.

## Roadmap

The current scope is vertical interpolation within individual float cycles
(depth-profile modeling). The next major milestone is extending this work to
**spatiotemporal interpolation across floats/buoys**, so predictions can use
both depth structure and cross-buoy spatial/temporal context.

## Current Pipeline (Cycle-Level)

For each cycle, the code follows this structure:

1. Resample observations onto a uniform pressure grid (`uniformed_pressure`).
2. Smooth readings and estimate curvature with Savitzky-Golay filtering.
3. Detect knot candidates from curvature peaks (`knot_identifier`).
4. Fit least-squares splines (`make_lsq_spline` / `LSQUnivariateSpline`).
5. Compute model error terms (training RMSE and/or fold-based error).
6. Query interpolated values and pressure-propagated uncertainty via `CycleModel`.

## Installation

### Option A: uv (recommended)

```bash
uv sync
```

### Option B: pip editable install

```bash
python -m pip install -e .
```

## Quick Start

```python
from argopy import DataFetcher as ArgoDataFetcher
from argo_interp.cycle import (
    CycleError,
    CycleModel,
    CycleSettings,
    ModelError,
    build_model,
    calc_fold_error,
)

# 1) Pull Argo data for a region/time box
box = [-75, -45, 20, 30, 0, 3000, "2011-01", "2011-06"]
argo_df = ArgoDataFetcher().region(box).load().data.to_dataframe()

# 2) Build per-cycle readings table
group_fields = ["PLATFORM_NUMBER", "CYCLE_NUMBER"]
readings = (
    argo_df[group_fields + ["PRES", "PSAL", "TEMP"]]
    .drop_duplicates()
    .sort_values([*group_fields, "PRES"])
    .reset_index(drop=True)
)
readings.insert(
    0,
    "PLATFORM_CYCLE",
    readings[group_fields[0]].astype(str) + "-" + readings[group_fields[1]].astype(str),
)
readings = readings.drop(columns=group_fields)

# 3) Fit cycle models
settings = CycleSettings(prominence=0.25, window=10, spacing=5.0, peak_dist=20, folds=5)
cycle_models: dict[str, CycleModel] = {}

for cycle_id, cycle_data in readings.groupby("PLATFORM_CYCLE"):
    cycle_data = cycle_data.sort_values("PRES")
    rmse_temp, rmse_sal = calc_fold_error(cycle_data, settings)

    cycle_model = CycleModel(
        temperature=build_model(cycle_data["PRES"], cycle_data["TEMP"], settings),
        salinity=build_model(cycle_data["PRES"], cycle_data["PSAL"], settings),
        error=CycleError(model=ModelError(temperature=rmse_temp, salinity=rmse_sal)),
        settings=settings,
        pressure_bounds=(float(cycle_data["PRES"].min()), float(cycle_data["PRES"].max())),
    )
    cycle_models[cycle_id] = cycle_model

# 4) Interpolate one cycle
example_cycle_id, example_model = next(iter(cycle_models.items()))
example_cycle_data = readings.loc[readings["PLATFORM_CYCLE"] == example_cycle_id]
results = example_model.interpolate(example_cycle_data["PRES"])
print(example_cycle_id)
print(results.head())
```

## Repository Layout

```text
src/argo_interp/cycle/
  CycleSettings.py      # Pydantic settings for smoothing, knot finding, CV folds
  CycleError.py         # Frozen dataclasses for model/sensor error components
  CycleModel.py         # Query interface for interpolation + propagated errors
  build_model.py        # End-to-end single-variable spline model construction
  build_spline_model.py # LSQ spline fitting
  knot_identifier.py    # Curvature-peak knot selection
  uniformed_pressure.py # Uniform pressure grid generator
  calc_fold_error.py    # Interleaved fold error estimation
  calc_rmse.py          # RMSE helper
```

## Data Notes

- Typical expected columns for cycle interpolation: `PRES`, `TEMP`, `PSAL`
- In current notebook usage, cycles are keyed by `PLATFORM_CYCLE`
- Pressure units are expected to be consistent across fitting/query steps

## License

Released under the terms of the GNU Affero General Public License v3.0.
See `LICENSE`.

## Acknowledgments

This work was inspired by participation in the 2025 MATE Floats workshop and
by the work of University of Washington Oceanography student Alnis Smidchens.
