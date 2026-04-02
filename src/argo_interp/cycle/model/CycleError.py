from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeasureError:
    sensor: float
    model: float


@dataclass(frozen=True, slots=True)
class CycleError:
    pressure: float
    temperature: MeasureError
    salinity: MeasureError
