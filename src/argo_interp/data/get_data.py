from argopy import DataFetcher
import xarray as xr

def get_data(box: list, progress: bool = False, max_workers: int = 4) -> xr.Dataset:
    f = DataFetcher(
        parallel=True,
        progress=progress,
        chunks_maxsize={"time": 120},
    ).region(box)
    ds = f.to_xarray(max_workers=max_workers)
    return ds
