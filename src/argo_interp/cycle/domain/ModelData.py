from dataclasses import dataclass
from typing import Self

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class ModelData:
    pressure: NDArray[np.float64]
    temperature: NDArray[np.float64]
    salinity: NDArray[np.float64]

    def __post_init__(self) -> None:
        if self.pressure.ndim != 1 or self.temperature.ndim != 1 or self.salinity.ndim != 1:
            raise ValueError("ModelData arrays must be one-dimensional")

        if len(self.temperature) != self.n_obs or len(self.salinity) != self.n_obs:
            raise ValueError("pressure, temperature, and salinity must have the same length")

    @property
    def n_obs(self) -> int:
        return len(self.pressure)

    def to_frame(self) -> pd.DataFrame:
        data_frame = pd.DataFrame(
            {
                "pressure": self.pressure,
                "temperature": self.temperature,
                "salinity": self.salinity,
            }
        )
        return data_frame

    @classmethod
    def from_frame(cls, data_frame: pd.DataFrame) -> Self:
        required = ["pressure", "temperature", "salinity"]
        missing = [col for col in required if col not in data_frame.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return cls(
            pressure=data_frame["pressure"].to_numpy(),
            temperature=data_frame["temperature"].to_numpy(),
            salinity=data_frame["salinity"].to_numpy(),
        )

    def clean_duplicates(self, rule: str = "error") -> Self:
        data_frame = self.to_frame().sort_values("pressure", kind="stable")

        if rule == "drop_exact":
            data_frame = data_frame.drop_duplicates(
                subset=["pressure", "temperature", "salinity"],
                keep="first",
            )
        elif rule == "first":
            data_frame = data_frame.drop_duplicates(subset=["pressure"], keep="first")
        elif rule == "mean":
            data_frame = data_frame.groupby("pressure", as_index=False).agg(
                {"temperature": "mean", "salinity": "mean"}
            )
        elif rule != "error":
            raise ValueError(f"Unknown duplicate_pressure policy: {rule}")

        pressure = data_frame["pressure"].to_numpy()
        if np.any(np.diff(pressure) <= 0):
            raise ValueError("pressure must be strictly increasing for fitting")

        return type(self).from_frame(data_frame)
