import xarray as xr
from argopy import DataFetcher


def get_data(box: list, progress: bool = False, max_workers: int = 4,
             mode: str = 'standard') -> xr.Dataset:
    f = DataFetcher(
        parallel=True,
        progress=progress,
        chunks_maxsize={"time": 180},
        mode=mode,
    ).region(box)
    ds = f.to_xarray(max_workers=max_workers)
    return ds
