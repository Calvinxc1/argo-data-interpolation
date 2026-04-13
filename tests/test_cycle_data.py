import numpy as np
import pandas as pd
import pytest

from argo_interp.model.CycleData import CycleData


def test_cycle_data_rejects_mismatched_pressure_index() -> None:
    temperature = pd.DataFrame({"cycle_a": [10.0, 11.0]}, index=pd.Index([1.0, 2.0], name="pressure"))
    salinity = pd.DataFrame({"cycle_a": [35.0, 35.1]}, index=pd.Index([1.0, 3.0], name="pressure"))

    with pytest.raises(ValueError, match="same pressure index"):
        CycleData(temperature=temperature, salinity=salinity)


def test_cycle_data_rejects_mismatched_cycle_columns() -> None:
    temperature = pd.DataFrame({"cycle_a": [10.0, 11.0]}, index=pd.Index([1.0, 2.0], name="pressure"))
    salinity = pd.DataFrame({"cycle_b": [35.0, 35.1]}, index=pd.Index([1.0, 2.0], name="pressure"))

    with pytest.raises(ValueError, match="same cycle columns"):
        CycleData(temperature=temperature, salinity=salinity)


def test_cycle_data_properties_and_frame_round_trip() -> None:
    temperature = pd.DataFrame(
        {"cycle_a": [10.0, 11.0], "cycle_b": [12.0, 13.0]},
        index=pd.Index([1.0, 2.0], name="pressure"),
    )
    salinity = pd.DataFrame(
        {"cycle_a": [35.0, 35.1], "cycle_b": [35.2, 35.3]},
        index=pd.Index([1.0, 2.0], name="pressure"),
    )
    cycle_data = CycleData(temperature=temperature, salinity=salinity)

    assert len(cycle_data) == 2
    assert cycle_data.n_obs == 2
    assert cycle_data.n_cycles == 2
    np.testing.assert_array_equal(cycle_data.pressure, np.array([1.0, 2.0]))
    pd.testing.assert_index_equal(cycle_data.cycle_ids, pd.Index(["cycle_a", "cycle_b"]))

    frame = cycle_data.to_frame()
    assert isinstance(frame.columns, pd.MultiIndex)
    assert set(frame.columns.get_level_values(0)) == {"temperature", "salinity"}

    restored = CycleData.from_frame(frame)
    pd.testing.assert_frame_equal(restored.temperature, cycle_data.temperature)
    pd.testing.assert_frame_equal(restored.salinity, cycle_data.salinity)


def test_cycle_data_from_frame_rejects_non_multiindex_columns() -> None:
    frame = pd.DataFrame({"temperature": [10.0], "salinity": [35.0]})

    with pytest.raises(ValueError, match="MultiIndex"):
        CycleData.from_frame(frame)


def test_cycle_data_from_frame_rejects_missing_measure_columns() -> None:
    frame = pd.concat(
        {"temperature": pd.DataFrame({"cycle_a": [10.0]}, index=pd.Index([1.0], name="pressure"))},
        axis=1,
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        CycleData.from_frame(frame)
