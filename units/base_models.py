# units/base_models.py

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Type, overload, Self

from units.dimensions import Dimension
from units.registry import resolve_dimension, register_dimension


class BaseUnit(Enum):
    def __init__(self, display: str, factor: float):
        self.display = display
        self.factor = factor

    def __str__(self):
        return self.display


# ----------------------------
# Metaclass
# ----------------------------


class MeasureMeta(type):
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)

        dim = namespace.get("dimension")
        if dim is not None:
            register_dimension(dim, cls)

        return cls

    def __getattr__(cls, name):
        enum_cls = cls.__dict__.get("_unit_enum")

        if enum_cls is None:
            raise AttributeError

        if name in enum_cls.__members__:
            unit = enum_cls[name]

            def factory(value: float):
                return cls(value, unit)

            return factory

        raise AttributeError(f"{name} not valid for {cls.__name__}")


# ----------------------------
# BaseMeasure
# ----------------------------


@dataclass(frozen=True)
class BaseMeasure(metaclass=MeasureMeta):
    value: float
    dimension: Dimension
    _unit_enum: Type[BaseUnit]
    user_unit: BaseUnit

    def __init__(self, value: float, unit: BaseUnit | str):
        cls = self.__class__

        if not hasattr(cls, "_unit_enum") or not hasattr(cls, "dimension"):
            raise TypeError(f"{cls.__name__} must define _unit_enum and dimension")

        unit_enum = cls._unit_enum

        # resolve unit
        if isinstance(unit, str):
            if unit in unit_enum.__members__:
                unit = unit_enum[unit]
            else:
                for m in unit_enum:
                    if m.display == unit:
                        unit = m
                        break
                else:
                    raise ValueError(f"Invalid unit '{unit}'")

        # store base units
        base_value = value * unit.factor

        object.__setattr__(self, "value", base_value)
        object.__setattr__(self, "dimension", cls.dimension)
        object.__setattr__(self, "_unit_enum", unit_enum)
        object.__setattr__(self, "user_unit", unit)

    # ----------------------------
    # Formatting
    # ----------------------------

    def __repr__(self):
        val = self.value / self.user_unit.factor
        return f"{val:g} {self.user_unit.display}"

    def __format__(self, format_spec: str):
        val = self.value / self.user_unit.factor
        return format(val, format_spec)

    # ----------------------------
    # Conversion
    # ----------------------------

    def to(self, unit: BaseUnit | str):
        unit_enum = self._unit_enum

        # resolve string → enum
        if isinstance(unit, str):
            if unit in unit_enum.__members__:
                unit = unit_enum[unit]
            else:
                for m in unit_enum:
                    if m.display == unit:
                        unit = m
                        break
                else:
                    raise ValueError(f"Invalid unit '{unit}'")

        # validate
        if not isinstance(unit, unit_enum):
            raise TypeError("Invalid unit")

        return self.__class__(self.value / unit.factor, unit)

    def _resolve(self, value: float, dim: Dimension):
        cls = resolve_dimension(dim)

        if cls is None:
            raise TypeError(
                f"Cannot resolve dimension {dim}. "
                f"This often happens due to operator precedence. "
                f"Try adding parentheses, e.g. s * (L / L) instead of s * L / L."
            )

        base_unit = min(cls._unit_enum, key=lambda u: u.factor)
        return cls(value / base_unit.factor, base_unit)

    # ----------------------------
    # Algebra
    # ----------------------------

    def __add__(self, other):
        if not isinstance(other, BaseMeasure):
            return NotImplemented

        if self.dimension != other.dimension:
            raise TypeError("Cannot add measures with different dimensions")

        base_sum = self.value + other.value
        return self.__class__(base_sum / self.user_unit.factor, self.user_unit)

    def __sub__(self, other):
        if not isinstance(other, BaseMeasure):
            return NotImplemented

        if self.dimension != other.dimension:
            raise TypeError("Cannot subtract measures with different dimensions")

        base_diff = self.value - other.value
        return self.__class__(base_diff / self.user_unit.factor, self.user_unit)

    @overload
    def __mul__(self, other: int | float) -> Self: ...

    @overload
    def __mul__(self, other: "BaseMeasure") -> BaseMeasure: ...

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(
                (self.value * other) / self.user_unit.factor, self.user_unit
            )

        if isinstance(other, BaseMeasure):
            return self._resolve(
                self.value * other.value,
                self.dimension * other.dimension,
            )

        return NotImplemented

    @overload
    def __truediv__(self, other: int | float) -> Self: ...

    @overload
    def __truediv__(self, other: "BaseMeasure") -> float | BaseMeasure: ...

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(
                (self.value / other) / self.user_unit.factor, self.user_unit
            )

        if isinstance(other, BaseMeasure):
            dim = self.dimension / other.dimension
            val = self.value / other.value

            if dim.is_dimensionless():
                return val

            return self._resolve(val, dim)

        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    # ----------------------------
    # Comparisons
    # ----------------------------

    def _cmp_value(self, other):
        if isinstance(other, BaseMeasure):
            if self.dimension != other.dimension:
                raise TypeError("Cannot compare different dimensions")
            return other.value  # already base units
        return float(other)

    def __eq__(self, other):
        try:
            return abs(self.value - self._cmp_value(other)) < 1e-9
        except TypeError:
            return False

    def __lt__(self, other):
        return self.value < self._cmp_value(other)

    def __le__(self, other):
        return self.value <= self._cmp_value(other)

    def __gt__(self, other):
        return self.value > self._cmp_value(other)

    def __ge__(self, other):
        return self.value >= self._cmp_value(other)
