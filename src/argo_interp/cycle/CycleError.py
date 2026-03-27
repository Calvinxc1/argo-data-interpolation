from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelError:
    temperature: float
    salinity: float

@dataclass(frozen=True, slots=True)
class SensorError:
    pressure: float = 2.4
    temperature: float = 0.002
    salinity: float = 0.01

@dataclass(frozen=True, slots=True)
class CycleError:
    model: ModelError
    sensor: SensorError = SensorError()
