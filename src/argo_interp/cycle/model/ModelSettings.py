from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelSettings:
    n_folds: int
    model_kwargs: dict[str, Any]
