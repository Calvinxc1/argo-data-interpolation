from dataclasses import dataclass

import pandas as pd

from .CycleData import CycleData


@dataclass(frozen=True, slots=True)
class MeasureVarianceData:
    sensor_precision: pd.DataFrame
    pressure_gradient: pd.DataFrame
    vertical_model: pd.DataFrame

    def __post_init__(self) -> None:
        frames = [self.sensor_precision, self.pressure_gradient, self.vertical_model]
        if any(not isinstance(frame, pd.DataFrame) for frame in frames):
            raise ValueError("MeasureVarianceData components must be pandas DataFrames")

        reference = self.sensor_precision
        for frame in frames[1:]:
            if not frame.index.equals(reference.index):
                raise ValueError("variance components must share the same pressure index")
            if not frame.columns.equals(reference.columns):
                raise ValueError("variance components must share the same cycle columns")

    @property
    def total(self) -> pd.DataFrame:
        return self.sensor_precision + self.pressure_gradient + self.vertical_model


@dataclass(frozen=True, slots=True)
class CycleVarianceData:
    temperature: MeasureVarianceData
    salinity: MeasureVarianceData

    def __post_init__(self) -> None:
        if not self.temperature.sensor_precision.index.equals(self.salinity.sensor_precision.index):
            raise ValueError("temperature and salinity variance data must share pressure index")
        if not self.temperature.sensor_precision.columns.equals(
            self.salinity.sensor_precision.columns
        ):
            raise ValueError("temperature and salinity variance data must share cycle columns")

    @property
    def total(self) -> CycleData:
        return CycleData(
            temperature=self.temperature.total,
            salinity=self.salinity.total,
        )
