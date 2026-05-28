from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

TimestampLike: TypeAlias = datetime | pd.Timestamp | np.datetime64 | str
FieldQueryLike: TypeAlias = "FieldQuery | tuple[float, float, TimestampLike, ArrayLike]"


@dataclass(frozen=True, slots=True)
class FieldQuery:
    latitude: float
    longitude: float
    timestamp: TimestampLike
    pressure: ArrayLike

    @classmethod
    def from_query(cls, query: FieldQueryLike) -> FieldQuery:
        if isinstance(query, cls):
            return query

        latitude, longitude, timestamp, pressure = query
        return cls(
            latitude=float(latitude),
            longitude=float(longitude),
            timestamp=timestamp,
            pressure=pressure,
        )

    def pressure_array(self) -> NDArray[np.float64]:
        pressure = np.asarray(self.pressure, dtype=float)
        if pressure.ndim == 0:
            pressure = pressure.reshape(1)
        if pressure.ndim != 1:
            raise ValueError("FieldQuery pressure must be scalar or one-dimensional")
        return pressure

    def timestamp64(self) -> np.datetime64:
        return pd.Timestamp(self.timestamp).to_datetime64()
