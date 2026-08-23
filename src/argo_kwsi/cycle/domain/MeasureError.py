from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeasureError:
    sensor: float
    model: float
