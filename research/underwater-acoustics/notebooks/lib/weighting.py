from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from argo_interp.model import CycleMetadata


AVERAGE_YEAR_SECONDS = 365.2425 * 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class GaussianScale:
    stdev: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.stdev) or self.stdev <= 0:
            raise ValueError("stdev must be a finite positive float")

    @classmethod
    def from_border(cls, border: float, border_stdev: float) -> "GaussianScale":
        if not np.isfinite(border) or border <= 0:
            raise ValueError("border must be a finite positive float")
        if not np.isfinite(border_stdev) or border_stdev <= 0:
            raise ValueError("border_stdev must be a finite positive float")
        return cls(stdev=border / border_stdev)

    def weight(self, x: ArrayLike | float) -> ArrayLike | float:
        x = np.asarray(x, dtype=float)
        return np.exp(-(x ** 2) / (2 * (self.stdev ** 2)))


@dataclass(frozen=True, slots=True)
class WeightDeltas:
    distance: np.ndarray
    time: np.ndarray
    season: np.ndarray

    def __post_init__(self) -> None:
        lengths = {len(self.distance), len(self.time), len(self.season)}
        if len(lengths) != 1:
            raise ValueError("Weight delta arrays must all have the same length")

    def __len__(self) -> int:
        return len(self.distance)


@dataclass(frozen=True, slots=True)
class WeightComponents:
    distance: np.ndarray
    time: np.ndarray
    season: np.ndarray

    def __post_init__(self) -> None:
        lengths = {len(self.distance), len(self.time), len(self.season)}
        if len(lengths) != 1:
            raise ValueError("Weight component arrays must all have the same length")

    def joint(self) -> np.ndarray:
        return self.distance * self.time * self.season


@dataclass(frozen=True, slots=True)
class WeightConfig:
    distance: GaussianScale
    time: GaussianScale
    season: GaussianScale
    use_distance: bool = True
    use_time: bool = True
    use_season: bool = True
    distance_power: float = 1.0
    time_power: float = 1.0
    season_power: float = 1.0

    def __post_init__(self) -> None:
        powers = (self.distance_power, self.time_power, self.season_power)
        if any((not np.isfinite(power)) or power <= 0 for power in powers):
            raise ValueError("weight powers must be finite positive floats")

    def component_weights(self, deltas: WeightDeltas) -> WeightComponents:
        size = len(deltas)
        return WeightComponents(
            distance=(
                np.power(self.distance.weight(deltas.distance), self.distance_power)
                if self.use_distance
                else np.ones(size, dtype=float)
            ),
            time=(
                np.power(self.time.weight(deltas.time), self.time_power)
                if self.use_time
                else np.ones(size, dtype=float)
            ),
            season=(
                np.power(self.season.weight(deltas.season), self.season_power)
                if self.use_season
                else np.ones(size, dtype=float)
            ),
        )

    def joint_weight(self, deltas: WeightDeltas) -> np.ndarray:
        total_weight = self.component_weights(deltas).joint()
        # total_weight /= total_weight.sum()
        return total_weight


def season_fraction(timestamp: np.datetime64 | np.ndarray) -> float | np.ndarray:
    timestamp_array = np.atleast_1d(np.asarray(timestamp, dtype="datetime64[ns]"))
    datetime_index = pd.to_datetime(timestamp_array)
    year_period = datetime_index.to_period("Y")
    year_start = year_period.start_time
    next_year_start = (year_period + 1).start_time

    elapsed = (datetime_index - year_start) / np.timedelta64(1, "s")
    year_length = (next_year_start - year_start) / np.timedelta64(1, "s")
    fraction = np.asarray(elapsed / year_length, dtype=float)

    if np.ndim(timestamp) == 0:
        return float(fraction[0])
    return fraction


def seasonal_distance_seconds(
    target_timestamp: np.datetime64,
    candidate_timestamps: np.ndarray,
) -> np.ndarray:
    target_fraction = season_fraction(target_timestamp)
    candidate_fraction = season_fraction(candidate_timestamps)
    wrapped_fraction_delta = np.abs(candidate_fraction - target_fraction)
    wrapped_fraction_delta = np.minimum(wrapped_fraction_delta, 1.0 - wrapped_fraction_delta)
    return wrapped_fraction_delta * AVERAGE_YEAR_SECONDS


def compute_weight_deltas(
    target_latitude: float,
    target_longitude: float,
    target_timestamp: np.datetime64,
    candidate_metadata: CycleMetadata,
) -> WeightDeltas:
    if len(candidate_metadata) == 0:
        empty = np.array([], dtype=float)
        return WeightDeltas(distance=empty, time=empty, season=empty)

    distance_delta = np.sqrt(
        np.square(candidate_metadata.latitude - target_latitude)
        + np.square(candidate_metadata.longitude - target_longitude)
    )
    time_delta = (
        candidate_metadata.timestamp - target_timestamp
    ) / np.timedelta64(1, "s")
    season_delta = seasonal_distance_seconds(
        target_timestamp=target_timestamp,
        candidate_timestamps=candidate_metadata.timestamp,
    )

    return WeightDeltas(
        distance=np.asarray(distance_delta, dtype=float),
        time=np.asarray(time_delta, dtype=float),
        season=np.asarray(season_delta, dtype=float),
    )
