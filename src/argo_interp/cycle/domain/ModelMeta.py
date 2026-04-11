from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ModelMeta:
    cycle_id: str
    latitude: float
    longitude: float
    timestamp: np.datetime64
    profile_pressure: tuple[float, float]
