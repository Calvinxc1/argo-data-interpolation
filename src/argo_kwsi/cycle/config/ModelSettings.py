from dataclasses import dataclass, field

from .ModelKwargs import ModelKwargs
from .SensorAccuracy import SensorAccuracy


@dataclass(frozen=True, slots=True)
class ModelSettings:
    n_folds: int
    model_kwargs: ModelKwargs = field(default_factory=ModelKwargs)
    sensor_accuracy: SensorAccuracy = field(default_factory=SensorAccuracy)
