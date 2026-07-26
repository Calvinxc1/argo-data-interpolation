from .data_filter import data_filter

__all__ = ["data_filter", "get_data"]


def __getattr__(name: str):
    if name == "get_data":
        from .get_data import get_data

        return get_data
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
