from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from ..collection import CycleBatch, CycleCollection, CycleIndex
from ..cycle.domain import ModelData
from ..cycle.validation.InterleavedKFolds import InterleavedKFolds
from .FieldProfile import FieldProfile
from .FieldQuery import FieldQuery, FieldQueryLike

_EARTH_RADIUS_KM = 6371.0088
_AVERAGE_YEAR_DAYS = 365.2425


class ProgressBar(Protocol):
    total: int | None

    def update(self, n: int = 1) -> object: ...
    def refresh(self) -> object: ...


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
    model_error: ModelData | None = None

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
        queries: FieldQueryLike | Iterable[FieldQueryLike],
    ) -> FieldProfile:
        return self._interpolate_queries(self._normalize_queries(queries))

    def _interpolate_queries(
        self,
        normalized_queries: list[FieldQuery],
        *,
        skip_out_of_domain: bool = False,
    ) -> FieldProfile:
        grouped_queries = self._group_queries_by_pressure(normalized_queries)
        profiles = []
        for pressure, indexed_queries in grouped_queries:
            profiles.extend(
                self._interpolate_query_group(
                    pressure,
                    indexed_queries,
                    skip_out_of_domain=skip_out_of_domain,
                )
            )
        return FieldProfile.concat(profiles)

    def cross_validate(
        self,
        pressure: ArrayLike,
        n_folds: int,
        pbar: ProgressBar | None = None,
    ) -> ModelData:
        """Estimate pressure-indexed field reconstruction RMSE.

        Held-out cycles are evaluated through their cycle interpolation models
        at the requested pressure grid, then compared against field predictions
        built from the remaining cycles. The returned error is therefore a
        cross-validated field reconstruction error against held-out cycle
        models, not a direct residual against raw native-pressure observations.
        It can retain some cycle-model uncertainty; callers that merge this
        with cycle and field spread errors should keep those components
        separate in outputs.
        """
        pressure_values = np.asarray(pressure, dtype=float)
        if pressure_values.ndim == 0:
            pressure_values = pressure_values.reshape(1)
        if pressure_values.ndim != 1:
            raise ValueError("pressure must be a one-dimensional array")

        k_folds = InterleavedKFolds(len(self.cycles), n_folds)
        temperature_sse = np.zeros(len(pressure_values), dtype=float)
        salinity_sse = np.zeros(len(pressure_values), dtype=float)
        valid_count = np.zeros(len(pressure_values), dtype=int)
        cycle_index = self.cycles.index()
        self._set_progress_total(pbar, self._cross_validation_total(k_folds, n_folds))

        for fold in range(n_folds):
            _, valid_mask = k_folds.fold_mask(fold)
            if not np.any(valid_mask):
                continue

            validation_cycle_ids = cycle_index.cycle_id[valid_mask].tolist()
            validation_field = self._copy_with_cycles(
                self.cycles.filter(
                    exclude_cycle_ids=validation_cycle_ids,
                    return_models_dict=True,
                )
            )
            validation_cycles = [self.cycles[cycle_id] for cycle_id in validation_cycle_ids]
            validation_queries = [
                FieldQuery(
                    latitude=cycle.meta.latitude,
                    longitude=cycle.meta.longitude,
                    timestamp=cycle.meta.timestamp,
                    pressure=pressure_values[
                        (pressure_values >= cycle.meta.profile_pressure[0])
                        & (pressure_values <= cycle.meta.profile_pressure[1])
                    ],
                )
                for cycle in validation_cycles
            ]
            actual = self.cycles.interpolate(pressure_values, mask=valid_mask)
            actual_temperature = actual.temperature.to_numpy(copy=False)
            actual_salinity = actual.salinity.to_numpy(copy=False)
            predicted = validation_field._interpolate_queries(
                validation_queries,
                skip_out_of_domain=True,
            )
            predicted_frame = predicted.to_frame()

            for query_index, cycle in enumerate(validation_cycles):
                query_pressure = validation_queries[query_index].pressure_array()
                pressure_mask = np.isin(pressure_values, query_pressure)
                if not np.any(pressure_mask):
                    continue

                query_prediction = predicted_frame[predicted_frame["query_index"] == query_index]
                if query_prediction.empty:
                    continue

                predicted_temperature = query_prediction["temperature"].to_numpy()
                predicted_salinity = query_prediction["salinity"].to_numpy()
                pressure_positions = np.flatnonzero(pressure_mask)
                actual_temperature_values = actual_temperature[
                    pressure_positions,
                    query_index,
                ]
                actual_salinity_values = actual_salinity[
                    pressure_positions,
                    query_index,
                ]
                finite_mask = (
                    np.isfinite(actual_temperature_values)
                    & np.isfinite(actual_salinity_values)
                    & np.isfinite(predicted_temperature)
                    & np.isfinite(predicted_salinity)
                )
                if not np.any(finite_mask):
                    continue

                pressure_positions = pressure_positions[finite_mask]
                temperature_error = (
                    actual_temperature_values[finite_mask] - predicted_temperature[finite_mask]
                )
                salinity_error = (
                    actual_salinity_values[finite_mask] - predicted_salinity[finite_mask]
                )
                temperature_sse[pressure_positions] += np.square(temperature_error)
                salinity_sse[pressure_positions] += np.square(salinity_error)
                valid_count[pressure_positions] += 1

            if pbar is not None:
                pbar.update(1)

        temperature_rmse = np.full(len(pressure_values), np.nan, dtype=float)
        salinity_rmse = np.full(len(pressure_values), np.nan, dtype=float)
        np.divide(
            temperature_sse,
            valid_count,
            out=temperature_rmse,
            where=valid_count > 0,
        )
        np.divide(
            salinity_sse,
            valid_count,
            out=salinity_rmse,
            where=valid_count > 0,
        )
        temperature_rmse = np.sqrt(temperature_rmse)
        salinity_rmse = np.sqrt(salinity_rmse)
        return ModelData(
            pressure=pressure_values.copy(),
            temperature=temperature_rmse,
            salinity=salinity_rmse,
        )

    def with_model_error(self, model_error: ModelData) -> LocalWeightedField:
        return type(self)(
            cycles=self.cycles,
            spatial_scale_km=self.spatial_scale_km,
            temporal_scale_days=self.temporal_scale_days,
            seasonal_scale_days=self.seasonal_scale_days,
            spatial_radius_km=self.spatial_radius_km,
            temporal_radius_days=self.temporal_radius_days,
            seasonal_radius_days=self.seasonal_radius_days,
            min_support=self.min_support,
            model_error=model_error,
        )

    @staticmethod
    def _cross_validation_total(k_folds: InterleavedKFolds, n_folds: int) -> int:
        return sum(int(np.any(k_folds.fold_mask(fold)[1])) for fold in range(n_folds))

    @staticmethod
    def _set_progress_total(pbar: ProgressBar | None, total: int) -> None:
        if pbar is None or getattr(pbar, "total", None) is not None:
            return

        pbar.total = total
        pbar.refresh()

    def _copy_with_cycles(self, models: dict[str, object]) -> LocalWeightedField:
        return type(self)(
            cycles=CycleCollection(models=models),
            spatial_scale_km=self.spatial_scale_km,
            temporal_scale_days=self.temporal_scale_days,
            seasonal_scale_days=self.seasonal_scale_days,
            spatial_radius_km=self.spatial_radius_km,
            temporal_radius_days=self.temporal_radius_days,
            seasonal_radius_days=self.seasonal_radius_days,
            min_support=self.min_support,
            model_error=None,
        )

    def _interpolate_one(
        self,
        query_index: int,
        query: FieldQuery,
    ) -> FieldProfile:
        latitude = float(query.latitude)
        longitude = float(query.longitude)
        timestamp = query.timestamp64()
        pressure = query.pressure_array()

        self._validate_query_domain(latitude, longitude, timestamp)
        mask = self._support_mask(latitude, longitude, timestamp)
        support_index = self.cycles.index(mask)

        if len(support_index) == 0:
            return self._empty_profile(query_index, latitude, longitude, timestamp, pressure)

        interpolates = self.cycles.interpolate(pressure, mask=mask)
        interp_errors = self.cycles.interp_error(pressure, mask=mask)
        weights = self._cycle_weights(latitude, longitude, timestamp, support_index)

        return self._combine(
            query_index,
            latitude,
            longitude,
            timestamp,
            pressure,
            support_index,
            weights,
            interpolates,
            interp_errors,
        )

    def _interpolate_query_group(
        self,
        pressure: NDArray[np.float64],
        indexed_queries: list[tuple[int, FieldQuery]],
        *,
        skip_out_of_domain: bool = False,
    ) -> list[FieldProfile]:
        if not indexed_queries:
            return []

        index = self.cycles.index()
        latitudes = np.array([query.latitude for _, query in indexed_queries], dtype=float)
        longitudes = np.array([query.longitude for _, query in indexed_queries], dtype=float)
        timestamps = np.array(
            [query.timestamp64() for _, query in indexed_queries],
            dtype="datetime64[ns]",
        )
        in_domain = self._validate_query_domains(latitudes, longitudes, timestamps)

        if not np.all(in_domain) and not skip_out_of_domain:
            invalid_position = int(np.flatnonzero(~in_domain)[0])
            self._validate_query_domain(
                float(latitudes[invalid_position]),
                float(longitudes[invalid_position]),
                timestamps[invalid_position],
            )

        if not np.any(in_domain):
            return []

        base_support, weights = self._query_cycle_support_and_weights(
            latitudes[in_domain],
            longitudes[in_domain],
            timestamps[in_domain],
            index,
        )
        interpolates = self.cycles.interpolate(pressure)
        interp_errors = self.cycles.interp_error(pressure)
        profiles: list[FieldProfile] = []
        valid_position = 0

        for position, (query_index, query) in enumerate(indexed_queries):
            if not in_domain[position]:
                continue

            profiles.append(
                self._combine(
                    query_index,
                    float(query.latitude),
                    float(query.longitude),
                    query.timestamp64(),
                    pressure,
                    index,
                    weights[valid_position],
                    interpolates,
                    interp_errors,
                    base_support=base_support[valid_position],
                )
            )
            valid_position += 1

        return profiles

    @staticmethod
    def _group_queries_by_pressure(
        queries: list[FieldQuery],
    ) -> list[tuple[NDArray[np.float64], list[tuple[int, FieldQuery]]]]:
        grouped: dict[
            tuple[float, ...],
            tuple[NDArray[np.float64], list[tuple[int, FieldQuery]]],
        ] = {}
        for query_index, query in enumerate(queries):
            pressure = query.pressure_array()
            key = tuple(pressure.tolist())
            if key not in grouped:
                grouped[key] = (pressure, [])
            grouped[key][1].append((query_index, query))
        return list(grouped.values())

    @staticmethod
    def _normalize_queries(
        queries: FieldQueryLike | Iterable[FieldQueryLike],
    ) -> list[FieldQuery]:
        if isinstance(queries, FieldQuery):
            return [queries]
        if isinstance(queries, tuple) and len(queries) == 4:
            return [FieldQuery.from_query(queries)]
        return [FieldQuery.from_query(query) for query in queries]

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

    def _validate_query_domains(
        self,
        latitudes: NDArray[np.float64],
        longitudes: NDArray[np.float64],
        timestamps: NDArray[np.datetime64],
    ) -> NDArray[np.bool_]:
        if len(self.cycles) == 0:
            raise ValueError("cannot interpolate from an empty CycleCollection")

        index = self.cycles.index()
        lat_min = float(np.nanmin(index.latitude))
        lat_max = float(np.nanmax(index.latitude))
        lon_min = float(np.nanmin(index.longitude))
        lon_max = float(np.nanmax(index.longitude))
        time_min = index.timestamp.min()
        time_max = index.timestamp.max()

        return (
            np.isfinite(latitudes)
            & (latitudes >= -90.0)
            & (latitudes <= 90.0)
            & np.isfinite(longitudes)
            & (longitudes >= -180.0)
            & (longitudes <= 180.0)
            & (latitudes >= lat_min)
            & (latitudes <= lat_max)
            & (longitudes >= lon_min)
            & (longitudes <= lon_max)
            & (timestamps >= time_min)
            & (timestamps <= time_max)
        )

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

    def _query_cycle_support_and_weights(
        self,
        latitudes: NDArray[np.float64],
        longitudes: NDArray[np.float64],
        timestamps: NDArray[np.datetime64],
        index: CycleIndex,
    ) -> tuple[NDArray[np.bool_], NDArray[np.float64]]:
        distance = self._distance_matrix_km(latitudes, longitudes, index)
        exponent = -0.5 * np.square(distance / self.spatial_scale_km)
        support = np.ones_like(exponent, dtype=bool)

        if self.spatial_radius_km is not None:
            support &= distance <= self.spatial_radius_km

        if self.temporal_scale_days is not None or self.temporal_radius_days is not None:
            delta_days = self._time_delta_matrix_days(timestamps, index.timestamp)
            if self.temporal_scale_days is not None:
                exponent += -0.5 * np.square(delta_days / self.temporal_scale_days)
            if self.temporal_radius_days is not None:
                support &= np.abs(delta_days) <= self.temporal_radius_days

        if self.seasonal_scale_days is not None or self.seasonal_radius_days is not None:
            season_days = self._seasonal_delta_matrix_days(timestamps, index.timestamp)
            if self.seasonal_scale_days is not None:
                exponent += -0.5 * np.square(season_days / self.seasonal_scale_days)
            if self.seasonal_radius_days is not None:
                support &= season_days <= self.seasonal_radius_days

        return support, np.where(support, np.exp(exponent), 0.0)

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
        query_index: int,
        latitude: float,
        longitude: float,
        timestamp: np.datetime64,
        pressure: NDArray[np.float64],
        index: CycleIndex,
        cycle_weights: NDArray[np.float64],
        interpolates: CycleBatch,
        interp_errors: CycleBatch,
        base_support: NDArray[np.bool_] | None = None,
    ) -> FieldProfile:
        support = (pressure[:, None] >= index.pressure_min[None, :]) & (
            pressure[:, None] <= index.pressure_max[None, :]
        )
        if base_support is not None:
            support &= base_support[None, :]
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

        temperature_values = interpolates.temperature.to_numpy(copy=False)
        salinity_values = interpolates.salinity.to_numpy(copy=False)
        temperature = self._weighted_mean(temperature_values, normalized)
        salinity = self._weighted_mean(salinity_values, normalized)
        temperature_cycle_error = self._weighted_cycle_error(
            interp_errors.temperature.to_numpy(copy=False),
            normalized,
        )
        salinity_cycle_error = self._weighted_cycle_error(
            interp_errors.salinity.to_numpy(copy=False),
            normalized,
        )
        temperature_field_error = self._weighted_field_error(
            temperature_values,
            normalized,
            temperature,
        )
        salinity_field_error = self._weighted_field_error(
            salinity_values,
            normalized,
            salinity,
        )
        temperature_model_error = self._model_error_for_pressure(pressure, "temperature")
        salinity_model_error = self._model_error_for_pressure(pressure, "salinity")
        temperature_error = np.sqrt(
            np.square(temperature_cycle_error)
            + np.square(temperature_field_error)
            + np.square(temperature_model_error)
        )
        salinity_error = np.sqrt(
            np.square(salinity_cycle_error)
            + np.square(salinity_field_error)
            + np.square(salinity_model_error)
        )

        temperature[~usable] = np.nan
        salinity[~usable] = np.nan
        temperature_error[~usable] = np.nan
        salinity_error[~usable] = np.nan
        temperature_cycle_error[~usable] = np.nan
        salinity_cycle_error[~usable] = np.nan
        temperature_field_error[~usable] = np.nan
        salinity_field_error[~usable] = np.nan
        temperature_model_error[~usable] = np.nan
        salinity_model_error[~usable] = np.nan

        return FieldProfile(
            query_index=np.full(len(pressure), query_index, dtype=int),
            latitude=np.full(len(pressure), latitude, dtype=float),
            longitude=np.full(len(pressure), longitude, dtype=float),
            timestamp=np.full(len(pressure), timestamp, dtype="datetime64[ns]"),
            pressure=pressure.copy(),
            temperature=temperature,
            salinity=salinity,
            temperature_error=temperature_error,
            salinity_error=salinity_error,
            temperature_cycle_error=temperature_cycle_error,
            salinity_cycle_error=salinity_cycle_error,
            temperature_field_error=temperature_field_error,
            salinity_field_error=salinity_field_error,
            temperature_model_error=temperature_model_error,
            salinity_model_error=salinity_model_error,
            support_count=np.asarray(support_count, dtype=int),
            support_weight=support_weight,
        )

    @staticmethod
    def _weighted_mean(
        values: NDArray[np.float64],
        normalized_weights: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        return np.nansum(values * normalized_weights, axis=1)

    @staticmethod
    def _weighted_cycle_error(
        errors: NDArray[np.float64],
        normalized_weights: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        cycle_variance = np.nansum(np.square(errors * normalized_weights), axis=1)
        return np.sqrt(cycle_variance)

    @staticmethod
    def _weighted_field_error(
        values: NDArray[np.float64],
        normalized_weights: NDArray[np.float64],
        weighted_mean: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        spread_variance = np.nansum(
            normalized_weights * np.square(values - weighted_mean[:, None]),
            axis=1,
        )
        return np.sqrt(spread_variance)

    def _model_error_for_pressure(
        self,
        pressure: NDArray[np.float64],
        measure: str,
    ) -> NDArray[np.float64]:
        if self.model_error is None:
            return np.zeros(len(pressure), dtype=float)

        if measure == "temperature":
            values = self.model_error.temperature
        else:
            values = self.model_error.salinity

        return np.interp(
            pressure,
            self.model_error.pressure,
            values,
            left=np.nan,
            right=np.nan,
        )

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
    def _distance_matrix_km(
        latitudes: NDArray[np.float64],
        longitudes: NDArray[np.float64],
        index: CycleIndex,
    ) -> NDArray[np.float64]:
        lat1 = np.deg2rad(latitudes)[:, None]
        lon1 = np.deg2rad(longitudes)[:, None]
        lat2 = np.deg2rad(index.latitude)[None, :]
        lon2 = np.deg2rad(index.longitude)[None, :]

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

    @staticmethod
    def _time_delta_matrix_days(
        timestamps: NDArray[np.datetime64],
        candidate_timestamps: NDArray[np.datetime64],
    ) -> NDArray[np.float64]:
        return np.asarray(
            (candidate_timestamps[None, :] - timestamps[:, None]) / np.timedelta64(1, "D"),
            dtype=float,
        )

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

    @classmethod
    def _seasonal_delta_matrix_days(
        cls,
        timestamps: NDArray[np.datetime64],
        candidate_timestamps: NDArray[np.datetime64],
    ) -> NDArray[np.float64]:
        target_fraction = np.asarray(cls._season_fraction(timestamps), dtype=float)[:, None]
        candidate_fraction = np.asarray(cls._season_fraction(candidate_timestamps), dtype=float)[
            None,
            :,
        ]
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
        query_index: int,
        latitude: float,
        longitude: float,
        timestamp: np.datetime64,
        pressure: NDArray[np.float64],
    ) -> FieldProfile:
        empty_float = np.full(len(pressure), np.nan, dtype=float)
        return FieldProfile(
            query_index=np.full(len(pressure), query_index, dtype=int),
            latitude=np.full(len(pressure), latitude, dtype=float),
            longitude=np.full(len(pressure), longitude, dtype=float),
            timestamp=np.full(len(pressure), timestamp, dtype="datetime64[ns]"),
            pressure=pressure.copy(),
            temperature=empty_float.copy(),
            salinity=empty_float.copy(),
            temperature_error=empty_float.copy(),
            salinity_error=empty_float.copy(),
            temperature_cycle_error=empty_float.copy(),
            salinity_cycle_error=empty_float.copy(),
            temperature_field_error=empty_float.copy(),
            salinity_field_error=empty_float.copy(),
            temperature_model_error=empty_float.copy(),
            salinity_model_error=empty_float.copy(),
            support_count=np.zeros(len(pressure), dtype=int),
            support_weight=np.zeros(len(pressure), dtype=float),
        )
