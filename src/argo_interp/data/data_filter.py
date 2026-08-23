from __future__ import annotations

import operator
from functools import reduce
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import xarray as xr


def data_filter(ds: xr.Dataset, filters: list[Any]) -> xr.Dataset:
    """Apply boolean masks to an xarray dataset.

    Xarray is provided by the optional ``argo-interp[data]`` extra.
    """

    mask = reduce(operator.and_, filters)
    return ds.where(mask, drop=True)
