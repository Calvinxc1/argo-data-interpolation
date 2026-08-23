"""Research-only cache and cycle-model helpers for the uncertainty product."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

from tqdm.auto import tqdm

from argo_kwsi.cycle.adapter import PchipAdapter
from argo_kwsi.cycle.config import ModelSettings
from argo_kwsi.cycle.domain import ModelData, ModelMeta
from argo_kwsi.cycle.model import Model
from argo_kwsi.data.data_filter import data_filter
from argo_kwsi.model import CycleModels


def cache_metadata_matches(
    metadata_path: Path, expected_metadata: dict[str, object]
) -> bool:
    if not metadata_path.exists():
        return False
    with metadata_path.open() as file:
        return json.load(file) == expected_metadata


def write_cache_metadata(metadata_path: Path, metadata: dict[str, object]) -> None:
    with metadata_path.open("w") as file:
        json.dump(metadata, file, indent=2, sort_keys=True)
        file.write("\n")


def load_filtered_argo_data(argo_data_path: Path, box: list[object]) -> Any:
    if argo_data_path.exists():
        with argo_data_path.open("rb") as file:
            dataset = pickle.load(file)
    else:
        from argo_kwsi.data.get_data import get_data

        dataset = get_data(box, progress=True)
        with argo_data_path.open("wb") as file:
            pickle.dump(dataset, file)

    dataset_filters = [
        dataset["PRES_QC"].isin([1, 2]),
        dataset["TEMP_QC"].isin([1, 2]),
        dataset["PSAL_QC"].isin([1, 2]),
    ]
    return data_filter(dataset, dataset_filters)


def build_cycle_models(
    filtered_dataset: Any, model_settings: ModelSettings
) -> tuple[CycleModels, dict[str, ModelData]]:
    models = {}
    models_data = {}

    cycles = len(
        filtered_dataset[["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"]]
        .to_dataframe()
        .drop_duplicates()
    )
    grouped = filtered_dataset.groupby(["PLATFORM_NUMBER", "CYCLE_NUMBER", "DIRECTION"])

    for (platform_number, cycle_number, direction), cycle_dataset in tqdm(
        grouped, total=cycles
    ):
        pressure = cycle_dataset["PRES"].values
        temperature = cycle_dataset["TEMP"].values
        salinity = cycle_dataset["PSAL"].values

        if cycle_dataset.sizes["N_POINTS"] < 3:
            continue

        model_data = ModelData(
            pressure=pressure,
            temperature=temperature,
            salinity=salinity,
        ).clean_duplicates("mean")

        model_meta = ModelMeta(
            platform_number=str(int(platform_number)),
            cycle_number=str(int(cycle_number)),
            direction=direction,
            latitude=cycle_dataset["LATITUDE"].values[0],
            longitude=cycle_dataset["LONGITUDE"].values[0],
            timestamp=cycle_dataset["TIME"].values[0],
            profile_pressure=(pressure.min(), pressure.max()),
        )

        model = Model.build(model_meta, model_data, PchipAdapter, model_settings)
        models[model_meta.cycle_id] = model
        models_data[model_meta.cycle_id] = model_data

    return CycleModels(models), models_data
