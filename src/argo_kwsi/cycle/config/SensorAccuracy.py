from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SensorAccuracy:
    pressure: float = 2.4
    temperature: float = 0.002
    salinity: float = 0.01
