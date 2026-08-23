from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class CycleMetadata:
    cycle_id: np.ndarray
    platform_number: np.ndarray
    cycle_number: np.ndarray
    direction: np.ndarray
    latitude: np.ndarray
    longitude: np.ndarray
    timestamp: np.ndarray
    seasonal_timestamp: np.ndarray
    pressure_min: np.ndarray
    pressure_max: np.ndarray

    def __post_init__(self) -> None:
        lengths = {
            len(self.cycle_id),
            len(self.platform_number),
            len(self.cycle_number),
            len(self.direction),
            len(self.latitude),
            len(self.longitude),
            len(self.timestamp),
            len(self.seasonal_timestamp),
            len(self.pressure_min),
            len(self.pressure_max),
        }
        if len(lengths) != 1:
            raise ValueError("CycleMetadata arrays must all have the same length")

    def __len__(self) -> int:
        return len(self.cycle_id)

    def select(self, mask: np.ndarray) -> CycleMetadata:
        return type(self)(
            cycle_id=self.cycle_id[mask],
            platform_number=self.platform_number[mask],
            cycle_number=self.cycle_number[mask],
            direction=self.direction[mask],
            latitude=self.latitude[mask],
            longitude=self.longitude[mask],
            timestamp=self.timestamp[mask],
            seasonal_timestamp=self.seasonal_timestamp[mask],
            pressure_min=self.pressure_min[mask],
            pressure_max=self.pressure_max[mask],
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "platform_number": self.platform_number,
                "cycle_number": self.cycle_number,
                "direction": self.direction,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "timestamp": self.timestamp,
                "pressure_min": self.pressure_min,
                "pressure_max": self.pressure_max,
            },
            index=pd.Index(self.cycle_id, name="cycle_id"),
        )
