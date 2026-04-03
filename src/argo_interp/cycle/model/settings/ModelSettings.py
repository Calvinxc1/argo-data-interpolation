from dataclasses import dataclass

from .ModelKwargs import ModelKwargs
from .SensorAccuracy import SensorAccuracy


@dataclass(frozen=True, slots=True)
class ModelSettings:
    n_folds: int
    model_kwargs: ModelKwargs = ModelKwargs()
    sensor_accuracy: SensorAccuracy = SensorAccuracy()
