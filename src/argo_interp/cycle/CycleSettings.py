from pydantic import BaseModel


class CycleSettings(BaseModel):
    prominence: float = 0.25
    window: int = 5
    spacing: float = 5.0
    peak_dist: int = 20
    folds: int = 5
