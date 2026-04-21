# units/registry.py

from typing import Type
from units.dimensions import Dimension

_DIMENSION_MAP: dict[Dimension, Type] = {}


def register_dimension(dim: Dimension, cls: Type):
    _DIMENSION_MAP[dim] = cls


def resolve_dimension(dim: Dimension):
    return _DIMENSION_MAP.get(dim)
