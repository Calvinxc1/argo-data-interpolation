from dataclasses import dataclass

from ..adapter.BaseAdapter import BaseAdapter


@dataclass(frozen=True, slots=True)
class ModelAdapters:
    temperature: BaseAdapter
    salinity: BaseAdapter
