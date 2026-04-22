import operator
from functools import reduce

import xarray as xr


def data_filter(ds: xr.Dataset, filters: list) -> xr.Dataset:
    mask = reduce(operator.and_, filters)
    filtered_ds = ds.where(mask, drop=True)
    return filtered_ds
