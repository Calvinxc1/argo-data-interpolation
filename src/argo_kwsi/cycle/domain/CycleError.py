from dataclasses import dataclass

from .MeasureError import MeasureError


@dataclass(frozen=True, slots=True)
class CycleError:
    pressure: float
    temperature: MeasureError
    salinity: MeasureError
