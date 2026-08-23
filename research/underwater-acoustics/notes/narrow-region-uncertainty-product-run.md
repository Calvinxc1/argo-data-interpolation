# BATS Reference-Region Uncertainty-Product Run

## Purpose and status

This is a recorded package run for a compact grid around the Bermuda Atlantic
Time-series Study (BATS) site in the Sargasso Sea. It demonstrates the
`SoundSpeedUncertaintyProduct` API after per-cycle models have been built. It
is a reproducibility example, not a validation against BATS shipboard data or
a claim about present-day Argo coverage.

BATS is a useful oceanographic reference case: it has collected physical,
biological, and chemical observations monthly since 1988, while nearby
Hydrostation S supplies a longer physical-oceanography record. [BIOS BATS
overview](https://bios.asu.edu/bats) [BIOS BATS and Hydrostation S
history](https://bios.asu.edu/bats/about) A published Argo analysis also
includes floats near BATS and the Hawaii Ocean Time-series site. [Johnson and
Bif (2021)](https://www.nature.com/articles/s41561-021-00807-z)

The query grid spans 0.4° by 0.4° at 0.1° spacing, covering 31.5–31.9°N and
64.4–64.0°W, centered on the BATS location at approximately 31.67°N, 64.17°W. The package query retrieved
52 profiles from 13 platforms in a wider 1.5° by 1.5° source box for
2018-01-01 through 2020-12-31 (accessed 2026-08-03).

## Configuration

The run uses the Notebook 6 target pressures (5, 35, 110, and 500 dbar), a
one-degree planar candidate radius, and its distance and temporal weighting.
The anchor time is 2019-07-01. Seasonal weighting is deliberately disabled:
the three-year local archive does not contain enough same-season profiles for
the narrow seasonal kernel to produce a useful spatial-support demonstration.
This is a local configuration choice, not a replacement for the Notebook 6
configuration.

## Package call

Run this from `research/underwater-acoustics/notebooks` after installing the
repository's development environment. `build_cycle_models` is research-only
support code used to turn the fetched xarray data into the package's
`CycleModels` input; the uncertainty product itself is the package API.

```python
from dataclasses import replace

import numpy as np

from argo_interp import (
    SoundSpeedUncertaintyConfig,
    SoundSpeedUncertaintyProduct,
    estimate_depthwise_spatial_variance,
)
from argo_interp.cycle.config import ModelSettings
from argo_interp.data import data_filter, get_data
from lib.product_support import build_cycle_models

source_box = [
    -65.0,
    -63.5,
    30.8,
    32.3,
    0.0,
    750.0,
    "2018-01-01",
    "2020-12-31",
]
dataset = get_data(source_box, progress=False, max_workers=1)
filtered = data_filter(
    dataset,
    [
        dataset["PRES_QC"].isin([1, 2]),
        dataset["TEMP_QC"].isin([1, 2]),
        dataset["PSAL_QC"].isin([1, 2]),
    ],
)
cycle_models, _ = build_cycle_models(filtered, ModelSettings(n_folds=5))

base_config = SoundSpeedUncertaintyConfig.notebook6()
config = replace(
    base_config,
    anchor_time="2019-07-01",
    weight_config=replace(base_config.weight_config, use_season=False),
)
spatial_variance = estimate_depthwise_spatial_variance(cycle_models, config)
product = SoundSpeedUncertaintyProduct(cycle_models, spatial_variance, config)

latitudes = np.array([31.5, 31.6, 31.7, 31.8, 31.9])
longitudes = np.array([-64.4, -64.3, -64.2, -64.1, -64.0])
result = product.grid(latitudes, longitudes)
```

`result` has 100 rows: 25 latitude/longitude query points times four target
pressures. Its provenance is available at
`result.attrs["argo_interp_uncertainty"]`.

## Recorded output

The following summary is from the package run above. Values are medians across
the 25 query points unless noted.

| Pressure (dbar) | Minimum candidates | Minimum effective cycles | Median effective cycles | Median sound speed (m/s) | Median sigma (m/s) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 46 | 17.371 | 21.673 | 1531.523374 | 6.927110 |
| 35 | 46 | 18.322 | 21.957 | 1531.569070 | 6.050611 |
| 110 | 46 | 17.452 | 21.239 | 1527.251643 | 2.140912 |
| 500 | 46 | 16.508 | 20.724 | 1520.901309 | 1.992477 |

At the grid point 31.5°N, 64.4°W, the output is:

| Pressure (dbar) | Sound speed (m/s) | Sigma (m/s) | Candidate cycles | Effective cycles | Display support |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 1532.999968 | 6.811853 | 52 | 30.356 | 0.311816 |
| 35 | 1532.440631 | 5.991908 | 52 | 30.397 | 0.311995 |
| 110 | 1527.281301 | 2.140221 | 52 | 29.426 | 0.302064 |
| 500 | 1520.674457 | 1.996261 | 52 | 28.671 | 0.289359 |

The relatively large shallow-pressure uncertainty is informative rather than a
failure of the example: the spatial-variance bucket was estimated from this
small local Argo archive. The BATS shipboard time series provides a natural
future independent comparison, but this run does not perform that comparison.

## Interpretation boundaries

- `depth_m` in the returned table currently mirrors `pressure_dbar`; it is not
  a physical-depth conversion.
- Sound-speed variance uses independent temperature and salinity terms. It
  excludes temperature-salinity covariance and TEOS-10 formula uncertainty.
- Argo holdings evolve. Re-running this query may return a different set of
  profiles, so the access date and source box are part of the recorded result.
