from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class CycleData:
    temperature: pd.DataFrame
    salinity: pd.DataFrame
