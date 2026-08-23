from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True, slots=True)
class ModelMeta:
    platform_number: str
    cycle_number: str
    direction: str
    latitude: float
    longitude: float
    timestamp: np.datetime64
    profile_pressure: tuple[float, float]
    _cycle_id_separator: str = field(default="-", repr=False)

    @property
    def cycle_id(self) -> str:
        return (
            f"{self.platform_number}"
            f"{self._cycle_id_separator}"
            f"{self.cycle_number}"
            f"{self._cycle_id_separator}"
            f"{self.direction}"
        )
