from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class FieldProfile:
    latitude: NDArray[np.float64]
    longitude: NDArray[np.float64]
    timestamp: NDArray[np.datetime64]
    pressure: NDArray[np.float64]
    temperature: NDArray[np.float64]
    salinity: NDArray[np.float64]
    temperature_error: NDArray[np.float64]
    salinity_error: NDArray[np.float64]
    support_count: NDArray[np.int_]
    support_weight: NDArray[np.float64]

    def __post_init__(self) -> None:
        axis_lengths = (
            len(self.latitude),
            len(self.longitude),
            len(self.timestamp),
            len(self.pressure),
        )
        expected_shape = axis_lengths

        for name in (
            "temperature",
            "salinity",
            "temperature_error",
            "salinity_error",
            "support_count",
            "support_weight",
        ):
            value = getattr(self, name)
            if value.shape != expected_shape:
                raise ValueError(f"{name} must have shape {expected_shape}")

    @property
    def shape(self) -> tuple[int, int, int, int]:
        return (
            len(self.latitude),
            len(self.longitude),
            len(self.timestamp),
            len(self.pressure),
        )

    def to_frame(self) -> pd.DataFrame:
        index = pd.MultiIndex.from_product(
            [
                range(len(self.latitude)),
                range(len(self.longitude)),
                range(len(self.timestamp)),
                range(len(self.pressure)),
            ],
            names=[
                "latitude_index",
                "longitude_index",
                "timestamp_index",
                "pressure_index",
            ],
        )
        frame = index.to_frame(index=False)

        frame["latitude"] = self.latitude[frame["latitude_index"].to_numpy()]
        frame["longitude"] = self.longitude[frame["longitude_index"].to_numpy()]
        frame["timestamp"] = self.timestamp[frame["timestamp_index"].to_numpy()]
        frame["pressure"] = self.pressure[frame["pressure_index"].to_numpy()]
        frame["temperature"] = self.temperature.ravel()
        frame["salinity"] = self.salinity.ravel()
        frame["temperature_error"] = self.temperature_error.ravel()
        frame["salinity_error"] = self.salinity_error.ravel()
        frame["support_count"] = self.support_count.ravel()
        frame["support_weight"] = self.support_weight.ravel()
        return frame
