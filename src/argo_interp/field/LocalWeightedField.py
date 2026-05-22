from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from ..collection import CycleBatch, CycleCollection, CycleIndex
from .FieldProfile import FieldProfile

TimestampLike = datetime | pd.Timestamp | np.datetime64 | str
QueryTimestampLike = TimestampLike | ArrayLike

_EARTH_RADIUS_KM = 6371.0088
_AVERAGE_YEAR_DAYS = 365.2425


@dataclass(frozen=True, slots=True)
class LocalWeightedField:
    cycles: CycleCollection
    spatial_scale_km: float
    temporal_scale_days: float | None = None
    seasonal_scale_days: float | None = None
    spatial_radius_km: float | None = None
    temporal_radius_days: float | None = None
    seasonal_radius_days: float | None = None
    min_support: int = 1

    def __post_init__(self) -> None:
        self._validate_positive("spatial_scale_km", self.spatial_scale_km)
        self._validate_optional_positive("temporal_scale_days", self.temporal_scale_days)
        self._validate_optional_positive("seasonal_scale_days", self.seasonal_scale_days)
        self._validate_optional_positive("spatial_radius_km", self.spatial_radius_km)
        self._validate_optional_positive("temporal_radius_days", self.temporal_radius_days)
        self._validate_optional_positive("seasonal_radius_days", self.seasonal_radius_days)
        if self.min_support < 1:
            raise ValueError("min_support must be at least 1")

    def interpolate(
        self,
        latitude: ArrayLike | float,
        longitude: ArrayLike | float,
        timestamp: QueryTimestampLike,
        pressure: ArrayLike,
    ) -> FieldProfile:
        pressure_values = np.asarray(pressure, dtype=float)
        if pressure_values.ndim == 0:
            pressure_values = pressure_values.reshape(1)
        if pressure_values.ndim != 1:
            raise ValueError("pressure must be a one-dimensional array")

        latitudes, longitudes, timestamps = self._normalize_query_points(
            latitude,
            longitude,
            timestamp,
        )

        shape = (len(latitudes), len(longitudes), len(timestamps), len(pressure_values))
        temperature = np.full(shape, np.nan, dtype=float)
        salinity = np.full(shape, np.nan, dtype=float)
        temperature_error = np.full(shape, np.nan, dtype=float)
        salinity_error = np.full(shape, np.nan, dtype=float)
        support_count = np.zeros(shape, dtype=int)
        support_weight = np.zeros(shape, dtype=float)

        for lat_pos, query_latitude in enumerate(latitudes):
            for lon_pos, query_longitude in enumerate(longitudes):
                for time_pos, query_timestamp in enumerate(timestamps):
                    profile = self._interpolate_one(
                        query_latitude,
                        query_longitude,
                        query_timestamp,
                        pressure_values,
                    )
                    result_slice = (lat_pos, lon_pos, time_pos, slice(None))
                    temperature[result_slice] = profile.temperature[0, 0, 0, :]
                    salinity[result_slice] = profile.salinity[0, 0, 0, :]
                    temperature_error[result_slice] = profile.temperature_error[0, 0, 0, :]
                    salinity_error[result_slice] = profile.salinity_error[0, 0, 0, :]
                    support_count[result_slice] = profile.support_count[0, 0, 0, :]
                    support_weight[result_slice] = profile.support_weight[0, 0, 0, :]

        return FieldProfile(
            latitude=latitudes.copy(),
            longitude=longitudes.copy(),
            timestamp=timestamps.copy(),
            pressure=pressure_values.copy(),
            temperature=temperature,
            salinity=salinity,
            temperature_error=temperature_error,
            salinity_error=salinity_error,
            support_count=support_count,
            support_weight=support_weight,
        )

    def _interpolate_one(
        self,
        latitude: float,
        longitude: float,
        target_timestamp: np.datetime64,
        pressure_values: NDArray[np.float64],
    ) -> FieldProfile:
        self._validate_query_domain(latitude, longitude, target_timestamp)
        mask = self._support_mask(latitude, longitude, target_timestamp)
        support_index = self.cycles.index(mask)

        if len(support_index) == 0:
            return self._empty_profile(latitude, longitude, target_timestamp, pressure_values)

        interpolates = self.cycles.interpolate(pressure_values, mask=mask)
        interp_errors = self.cycles.interp_error(pressure_values, mask=mask)
        weights = self._cycle_weights(latitude, longitude, target_timestamp, support_index)

        return self._combine(
            latitude,
            longitude,
            target_timestamp,
            pressure_values,
            support_index,
            weights,
            interpolates,
            interp_errors,
        )

    @staticmethod
    def _normalize_query_points(
        latitude: ArrayLike | float,
        longitude: ArrayLike | float,
        timestamp: QueryTimestampLike,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.datetime64]]:
        latitudes = np.asarray(latitude, dtype=float)
        longitudes = np.asarray(longitude, dtype=float)
        timestamps = pd.to_datetime(np.atleast_1d(timestamp)).to_numpy(dtype="datetime64[ns]")

        latitudes = np.atleast_1d(latitudes)
        longitudes = np.atleast_1d(longitudes)
        if latitudes.ndim != 1 or longitudes.ndim != 1:
            raise ValueError("latitude and longitude must be scalar or one-dimensional arrays")
        if timestamps.ndim != 1:
            raise ValueError("timestamp must be scalar or a one-dimensional array")

        return latitudes, longitudes, timestamps

    @staticmethod
    def _validate_positive(name: str, value: float) -> None:
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite positive float")

    @classmethod
    def _validate_optional_positive(cls, name: str, value: float | None) -> None:
        if value is not None:
            cls._validate_positive(name, value)

    def _validate_query_domain(
        self,
        latitude: float,
        longitude: float,
        timestamp: np.datetime64,
    ) -> None:
        if len(self.cycles) == 0:
            raise ValueError("cannot interpolate from an empty CycleCollection")
        if not np.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be a finite value between -90 and 90")
        if not np.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be a finite value between -180 and 180")

        index = self.cycles.index()
        lat_min = float(np.nanmin(index.latitude))
        lat_max = float(np.nanmax(index.latitude))
        lon_min = float(np.nanmin(index.longitude))
        lon_max = float(np.nanmax(index.longitude))
        time_min = index.timestamp.min()
        time_max = index.timestamp.max()

        if not lat_min <= latitude <= lat_max:
            raise ValueError(f"latitude must be within collection bounds [{lat_min}, {lat_max}]")
        if not lon_min <= longitude <= lon_max:
            raise ValueError(f"longitude must be within collection bounds [{lon_min}, {lon_max}]")
        if not time_min <= timestamp <= time_max:
            raise ValueError(f"timestamp must be within collection bounds [{time_min}, {time_max}]")

    def _support_mask(
        self,
        latitude: float,
        longitude: float,
        timestamp: np.datetime64,
    ) -> NDArray[np.bool_]:
        mask = np.ones(len(self.cycles), dtype=bool)
        index = self.cycles.index()

        if self.spatial_radius_km is not None:
            distance = self._distance_km(latitude, longitude, index)
            mask &= distance <= self.spatial_radius_km

        if self.temporal_radius_days is not None:
            delta_days = self._time_delta_days(timestamp, index.timestamp)
            mask &= np.abs(delta_days) <= self.temporal_radius_days

        if self.seasonal_radius_days is not None:
            season_days = self._seasonal_delta_days(timestamp, index.timestamp)
            mask &= season_days <= self.seasonal_radius_days

        return mask

    def _cycle_weights(
        self,
        latitude: float,
        longitude: float,
        timestamp: np.datetime64,
        index: CycleIndex,
    ) -> NDArray[np.float64]:
        distance = self._distance_km(latitude, longitude, index)
        exponent = -0.5 * np.square(distance / self.spatial_scale_km)

        if self.temporal_scale_days is not None:
            delta_days = self._time_delta_days(timestamp, index.timestamp)
            exponent += -0.5 * np.square(delta_days / self.temporal_scale_days)

        if self.seasonal_scale_days is not None:
            season_days = self._seasonal_delta_days(timestamp, index.timestamp)
            exponent += -0.5 * np.square(season_days / self.seasonal_scale_days)

        return np.exp(exponent)

    def _combine(
        self,
        latitude: float,
        longitude: float,
        timestamp: np.datetime64,
        pressure: NDArray[np.float64],
        index: CycleIndex,
        cycle_weights: NDArray[np.float64],
        interpolates: CycleBatch,
        interp_errors: CycleBatch,
    ) -> FieldProfile:
        support = (pressure[:, None] >= index.pressure_min[None, :]) & (
            pressure[:, None] <= index.pressure_max[None, :]
        )
        finite_temperature = np.isfinite(interpolates.temperature.to_numpy(copy=False))
        finite_salinity = np.isfinite(interpolates.salinity.to_numpy(copy=False))
        support &= finite_temperature & finite_salinity

        row_weights = np.where(support, cycle_weights[None, :], 0.0)
        support_count = support.sum(axis=1)
        support_weight = row_weights.sum(axis=1)
        usable = (support_count >= self.min_support) & (support_weight > 0)
        normalized = np.divide(
            row_weights,
            support_weight[:, None],
            out=np.zeros_like(row_weights, dtype=float),
            where=support_weight[:, None] > 0,
        )

        temperature = self._weighted_mean(interpolates.temperature.to_numpy(copy=False), normalized)
        salinity = self._weighted_mean(interpolates.salinity.to_numpy(copy=False), normalized)
        temperature_error = self._weighted_error(
            interp_errors.temperature.to_numpy(copy=False),
            normalized,
        )
        salinity_error = self._weighted_error(
            interp_errors.salinity.to_numpy(copy=False),
            normalized,
        )

        temperature[~usable] = np.nan
        salinity[~usable] = np.nan
        temperature_error[~usable] = np.nan
        salinity_error[~usable] = np.nan

        return FieldProfile(
            latitude=np.array([latitude], dtype=float),
            longitude=np.array([longitude], dtype=float),
            timestamp=np.array([timestamp], dtype="datetime64[ns]"),
            pressure=pressure.copy(),
            temperature=temperature.reshape(1, 1, 1, -1),
            salinity=salinity.reshape(1, 1, 1, -1),
            temperature_error=temperature_error.reshape(1, 1, 1, -1),
            salinity_error=salinity_error.reshape(1, 1, 1, -1),
            support_count=np.asarray(support_count, dtype=int).reshape(1, 1, 1, -1),
            support_weight=support_weight.reshape(1, 1, 1, -1),
        )

    @staticmethod
    def _weighted_mean(
        values: NDArray[np.float64],
        normalized_weights: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        return np.nansum(values * normalized_weights, axis=1)

    @staticmethod
    def _weighted_error(
        errors: NDArray[np.float64],
        normalized_weights: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        variance = np.nansum(np.square(errors * normalized_weights), axis=1)
        return np.sqrt(variance)

    @staticmethod
    def _distance_km(latitude: float, longitude: float, index: CycleIndex) -> NDArray[np.float64]:
        lat1 = np.deg2rad(latitude)
        lon1 = np.deg2rad(longitude)
        lat2 = np.deg2rad(index.latitude)
        lon2 = np.deg2rad(index.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.square(np.sin(dlat / 2.0)) + np.cos(lat1) * np.cos(lat2) * np.square(
            np.sin(dlon / 2.0)
        )
        return 2.0 * _EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))

    @staticmethod
    def _time_delta_days(
        timestamp: np.datetime64,
        candidate_timestamps: NDArray[np.datetime64],
    ) -> NDArray[np.float64]:
        return np.asarray((candidate_timestamps - timestamp) / np.timedelta64(1, "D"), dtype=float)

    @classmethod
    def _seasonal_delta_days(
        cls,
        timestamp: np.datetime64,
        candidate_timestamps: NDArray[np.datetime64],
    ) -> NDArray[np.float64]:
        target_fraction = cls._season_fraction(timestamp)
        candidate_fraction = cls._season_fraction(candidate_timestamps)
        fraction_delta = np.abs(candidate_fraction - target_fraction)
        fraction_delta = np.minimum(fraction_delta, 1.0 - fraction_delta)
        return fraction_delta * _AVERAGE_YEAR_DAYS

    @staticmethod
    def _season_fraction(
        timestamp: np.datetime64 | NDArray[np.datetime64],
    ) -> float | NDArray[np.float64]:
        timestamp_array = np.atleast_1d(np.asarray(timestamp, dtype="datetime64[ns]"))
        datetime_index = pd.to_datetime(timestamp_array)
        year_period = datetime_index.to_period("Y")
        year_start = year_period.start_time
        next_year_start = (year_period + 1).start_time

        elapsed = (datetime_index - year_start) / np.timedelta64(1, "D")
        year_length = (next_year_start - year_start) / np.timedelta64(1, "D")
        fraction = np.asarray(elapsed / year_length, dtype=float)

        if np.ndim(timestamp) == 0:
            return float(fraction[0])
        return fraction

    @staticmethod
    def _empty_profile(
        latitude: float,
        longitude: float,
        timestamp: np.datetime64,
        pressure: NDArray[np.float64],
    ) -> FieldProfile:
        empty_float = np.full(len(pressure), np.nan, dtype=float)
        return FieldProfile(
            latitude=np.array([latitude], dtype=float),
            longitude=np.array([longitude], dtype=float),
            timestamp=np.array([timestamp], dtype="datetime64[ns]"),
            pressure=pressure.copy(),
            temperature=empty_float.copy().reshape(1, 1, 1, -1),
            salinity=empty_float.copy().reshape(1, 1, 1, -1),
            temperature_error=empty_float.copy().reshape(1, 1, 1, -1),
            salinity_error=empty_float.copy().reshape(1, 1, 1, -1),
            support_count=np.zeros((1, 1, 1, len(pressure)), dtype=int),
            support_weight=np.zeros((1, 1, 1, len(pressure)), dtype=float),
        )
