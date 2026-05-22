from dataclasses import dataclass

from ..adapter.BaseAdapter import BaseAdapter


@dataclass(frozen=True, slots=True)
class InterpolationAdapters:
    temperature: BaseAdapter
    salinity: BaseAdapter
