import numpy as np
import pytest

from argo_interp.cycle.domain.ModelMeta import ModelMeta


def test_model_meta_exposes_structured_cycle_parts_and_derived_cycle_id() -> None:
    meta = ModelMeta(
        platform_number="5901234",
        cycle_number="17",
        direction="A",
        latitude=1.0,
        longitude=2.0,
        timestamp=np.datetime64("2026-01-01"),
        profile_pressure=(0.0, 100.0),
    )

    assert meta.platform_number == "5901234"
    assert meta.cycle_number == "17"
    assert meta.direction == "A"
    assert meta.cycle_id == "5901234-17-A"


def test_model_meta_uses_configured_cycle_id_separator() -> None:
    meta = ModelMeta(
        platform_number="5901234",
        cycle_number="17",
        direction="A",
        latitude=1.0,
        longitude=2.0,
        timestamp=np.datetime64("2026-01-01"),
        profile_pressure=(0.0, 100.0),
        _cycle_id_separator="|",
    )

    assert meta.cycle_id == "5901234|17|A"


def test_model_meta_rejects_cycle_id_input() -> None:
    with pytest.raises(TypeError):
        ModelMeta(
            cycle_id="5901234-17-A",
            latitude=1.0,
            longitude=2.0,
            timestamp=np.datetime64("2026-01-01"),
            profile_pressure=(0.0, 100.0),
        )
