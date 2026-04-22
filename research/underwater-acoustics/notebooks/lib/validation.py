from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta as td
from typing import Any

import pandas as pd


@dataclass(frozen=True, slots=True)
class CandidateQuery:
    lat: tuple[float, float] | None = None
    lon: tuple[float, float] | None = None
    cyclical_dates: tuple[pd.Timestamp, pd.Timestamp] | None = None
    exclude_platform_number: Any = None

    def to_mask_kwargs(self) -> dict[str, object]:
        mask_kwargs: dict[str, object] = {}
        if self.lat is not None:
            mask_kwargs["lat"] = self.lat
        if self.lon is not None:
            mask_kwargs["lon"] = self.lon
        if self.cyclical_dates is not None:
            mask_kwargs["cyclical_dates"] = self.cyclical_dates
        if self.exclude_platform_number is not None:
            mask_kwargs["exclude_platform_number"] = self.exclude_platform_number
        return mask_kwargs


def build_candidate_query(
    target_latitude: float | None = None,
    target_longitude: float | None = None,
    target_timestamp: pd.Timestamp | None = None,
    dist_rad: float | None = None,
    season_weeks: int | None = None,
    exclude_platform_number: Any = None,
) -> CandidateQuery:
    lat = None
    lon = None
    cyclical_dates = None

    using_spatial = any(value is not None for value in (target_latitude, target_longitude, dist_rad))
    if using_spatial:
        if target_latitude is None or target_longitude is None or dist_rad is None:
            raise ValueError("target_latitude, target_longitude, and dist_rad are all required for spatial filtering")
        lat = (target_latitude - dist_rad, target_latitude + dist_rad)
        lon = (target_longitude - dist_rad, target_longitude + dist_rad)

    using_seasonal = target_timestamp is not None or season_weeks is not None
    if using_seasonal:
        if target_timestamp is None or season_weeks is None:
            raise ValueError("target_timestamp and season_weeks are both required for seasonal filtering")
        cyclical_dates = (
            target_timestamp - td(weeks=season_weeks),
            target_timestamp + td(weeks=season_weeks),
        )

    return CandidateQuery(
        lat=lat,
        lon=lon,
        cyclical_dates=cyclical_dates,
        exclude_platform_number=exclude_platform_number,
    )
