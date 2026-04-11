import xarray as xr
from functools import reduce
import operator


def data_filter(ds: xr.Dataset, filters: list) -> xr.Dataset:
    mask = reduce(operator.and_, filters)
    filtered_ds = ds.where(mask, drop=True)
    return filtered_ds
