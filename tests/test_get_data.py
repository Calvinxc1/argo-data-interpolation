import sys
from types import ModuleType

import pytest
import xarray as xr

from argo_kwsi.data import get_data


class MockFetcher:
    def __init__(self, dataset: xr.Dataset) -> None:
        self.dataset = dataset
        self.region_box = None
        self.max_workers = None

    def region(self, box: list[float]) -> "MockFetcher":
        self.region_box = box
        return self

    def to_xarray(self, max_workers: int) -> xr.Dataset:
        self.max_workers = max_workers
        return self.dataset


def test_get_data_builds_fetcher_with_expected_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = xr.Dataset({"temperature": ("obs", [1.0, 2.0])})
    fetcher = MockFetcher(dataset)
    calls: dict[str, object] = {}

    def fake_data_fetcher(**kwargs: object) -> MockFetcher:
        calls.update(kwargs)
        return fetcher

    mock_argopy = ModuleType("argopy")
    mock_argopy.DataFetcher = fake_data_fetcher  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "argopy", mock_argopy)

    box = [0.0, 1.0, 2.0, 3.0, 0.0, 10.0]
    result = get_data(box=box, progress=True, max_workers=7, mode="expert")

    assert result is dataset
    assert fetcher.region_box == box
    assert fetcher.max_workers == 7
    assert calls == {
        "parallel": True,
        "progress": True,
        "chunks_maxsize": {"time": 180},
        "mode": "expert",
    }


def test_get_data_explains_how_to_install_the_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "argopy", None)

    with pytest.raises(ImportError, match="argo-kwsi\\[data\\]"):
        get_data(box=[0.0, 1.0, 2.0, 3.0, 0.0, 10.0])
