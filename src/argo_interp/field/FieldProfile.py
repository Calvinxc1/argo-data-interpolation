from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class FieldProfile:
    query_index: NDArray[np.int_]
    latitude: NDArray[np.float64]
    longitude: NDArray[np.float64]
    timestamp: NDArray[np.datetime64]
    pressure: NDArray[np.float64]
    temperature: NDArray[np.float64]
    salinity: NDArray[np.float64]
    temperature_error: NDArray[np.float64]
    salinity_error: NDArray[np.float64]
    temperature_cycle_error: NDArray[np.float64]
    salinity_cycle_error: NDArray[np.float64]
    temperature_field_error: NDArray[np.float64]
    salinity_field_error: NDArray[np.float64]
    temperature_model_error: NDArray[np.float64]
    salinity_model_error: NDArray[np.float64]
    support_count: NDArray[np.int_]
    support_weight: NDArray[np.float64]

    def __post_init__(self) -> None:
        expected_shape = self.query_index.shape
        if self.query_index.ndim != 1:
            raise ValueError("query_index must be one-dimensional")

        for name in (
            "latitude",
            "longitude",
            "timestamp",
            "pressure",
            "temperature",
            "salinity",
            "temperature_error",
            "salinity_error",
            "temperature_cycle_error",
            "salinity_cycle_error",
            "temperature_field_error",
            "salinity_field_error",
            "temperature_model_error",
            "salinity_model_error",
            "support_count",
            "support_weight",
        ):
            value = getattr(self, name)
            if value.shape != expected_shape:
                raise ValueError(f"{name} must have shape {expected_shape}")

    @property
    def shape(self) -> tuple[int]:
        return self.query_index.shape

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "query_index": self.query_index,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "timestamp": self.timestamp,
                "pressure": self.pressure,
                "temperature": self.temperature,
                "salinity": self.salinity,
                "temperature_error": self.temperature_error,
                "salinity_error": self.salinity_error,
                "temperature_cycle_error": self.temperature_cycle_error,
                "salinity_cycle_error": self.salinity_cycle_error,
                "temperature_field_error": self.temperature_field_error,
                "salinity_field_error": self.salinity_field_error,
                "temperature_model_error": self.temperature_model_error,
                "salinity_model_error": self.salinity_model_error,
                "support_count": self.support_count,
                "support_weight": self.support_weight,
            }
        )

    @classmethod
    def concat(cls, profiles: list["FieldProfile"]) -> "FieldProfile":
        if not profiles:
            empty_float = np.array([], dtype=float)
            return cls(
                query_index=np.array([], dtype=int),
                latitude=empty_float.copy(),
                longitude=empty_float.copy(),
                timestamp=np.array([], dtype="datetime64[ns]"),
                pressure=empty_float.copy(),
                temperature=empty_float.copy(),
                salinity=empty_float.copy(),
                temperature_error=empty_float.copy(),
                salinity_error=empty_float.copy(),
                temperature_cycle_error=empty_float.copy(),
                salinity_cycle_error=empty_float.copy(),
                temperature_field_error=empty_float.copy(),
                salinity_field_error=empty_float.copy(),
                temperature_model_error=empty_float.copy(),
                salinity_model_error=empty_float.copy(),
                support_count=np.array([], dtype=int),
                support_weight=empty_float.copy(),
            )

        return cls(
            query_index=np.concatenate([profile.query_index for profile in profiles]),
            latitude=np.concatenate([profile.latitude for profile in profiles]),
            longitude=np.concatenate([profile.longitude for profile in profiles]),
            timestamp=np.concatenate([profile.timestamp for profile in profiles]),
            pressure=np.concatenate([profile.pressure for profile in profiles]),
            temperature=np.concatenate([profile.temperature for profile in profiles]),
            salinity=np.concatenate([profile.salinity for profile in profiles]),
            temperature_error=np.concatenate([profile.temperature_error for profile in profiles]),
            salinity_error=np.concatenate([profile.salinity_error for profile in profiles]),
            temperature_cycle_error=np.concatenate(
                [profile.temperature_cycle_error for profile in profiles]
            ),
            salinity_cycle_error=np.concatenate(
                [profile.salinity_cycle_error for profile in profiles]
            ),
            temperature_field_error=np.concatenate(
                [profile.temperature_field_error for profile in profiles]
            ),
            salinity_field_error=np.concatenate(
                [profile.salinity_field_error for profile in profiles]
            ),
            temperature_model_error=np.concatenate(
                [profile.temperature_model_error for profile in profiles]
            ),
            salinity_model_error=np.concatenate(
                [profile.salinity_model_error for profile in profiles]
            ),
            support_count=np.concatenate([profile.support_count for profile in profiles]),
            support_weight=np.concatenate([profile.support_weight for profile in profiles]),
        )
