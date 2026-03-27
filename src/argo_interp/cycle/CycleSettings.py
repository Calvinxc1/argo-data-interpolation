from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CycleSettings:
    prominence: float = 0.25
    window: int = 5
    spacing: float = 5.0
    peak_dist: int = 20
    folds: int = 5
