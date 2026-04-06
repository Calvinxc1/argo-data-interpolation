from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class ModelKwargs:
    temperature: dict[str, Any] = field(default_factory=dict)
    salinity: dict[str, Any] = field(default_factory=dict)
