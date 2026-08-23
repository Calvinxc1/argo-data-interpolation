from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import xarray as xr


def get_data(
    box: list,
    progress: bool = False,
    max_workers: int = 4,
    mode: str = "standard",
) -> xr.Dataset:
    """Fetch Argo observations for a region.

    Requires the optional ``argo-interp[data]`` extra.
    """

    try:
        from argopy import DataFetcher
    except ModuleNotFoundError as error:
        raise ImportError(
            "Argo data fetching requires the 'data' extra: install argo-interp[data]."
        ) from error

    fetcher = DataFetcher(
        parallel=True,
        progress=progress,
        chunks_maxsize={"time": 180},
        mode=mode,
    ).region(box)
    return fetcher.to_xarray(max_workers=max_workers)
