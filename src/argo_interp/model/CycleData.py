from dataclasses import dataclass
from typing import Self

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class CycleData:
    temperature: pd.DataFrame
    salinity: pd.DataFrame

    def __post_init__(self) -> None:
        if (
            not isinstance(self.temperature, pd.DataFrame)
            or not isinstance(self.salinity, pd.DataFrame)
        ):
            raise ValueError("CycleData temperature and salinity must be pandas DataFrames")

        if not self.temperature.index.equals(self.salinity.index):
            raise ValueError("temperature and salinity must share the same pressure index")

        if not self.temperature.columns.equals(self.salinity.columns):
            raise ValueError("temperature and salinity must share the same cycle columns")

    def __len__(self) -> int:
        return self.n_obs

    @property
    def n_obs(self) -> int:
        return len(self.temperature.index)

    @property
    def n_cycles(self) -> int:
        return len(self.temperature.columns)

    @property
    def pressure(self) -> np.ndarray:
        return self.temperature.index.to_numpy(copy=True)

    @property
    def cycle_ids(self) -> pd.Index:
        return self.temperature.columns.copy()

    def to_frame(self) -> pd.DataFrame:
        data_frame = pd.concat(
            {
                "temperature": self.temperature,
                "salinity": self.salinity,
            },
            axis=1,
        )
        return data_frame

    @classmethod
    def from_frame(cls, data_frame: pd.DataFrame) -> Self:
        if not isinstance(data_frame.columns, pd.MultiIndex):
            raise ValueError("CycleData frame must use a MultiIndex column layout")

        required = ["temperature", "salinity"]
        missing = [name for name in required if name not in data_frame.columns.get_level_values(0)]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return cls(
            temperature=data_frame["temperature"].copy(),
            salinity=data_frame["salinity"].copy(),
        )
