from argopy import DataFetcher
import xarray as xr

def get_data(box: list) -> xr.Dataset:
    f = DataFetcher().region(box).load()
    ds = f.to_xarray()
    return ds
