from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import overload, Any
from typing_extensions import Self

from units.dimensions import Dimension

# import numpy as np


# T = TypeVar("T", bound="BaseTensor")


class BaseUnit(Enum):
    """
    Base class for all physical quantity units.
    """

    def __init__(self, display: str, factor: float):
        self.display = display
        self.factor = factor

    def __str__(self):
        return self.display

    def __repr__(self):
        # New format: <Unit: MPa>
        return f"<{self.__class__.__name__}.{self.name}: {self.display}>"


@dataclass(frozen=True)
class BaseMeasure:
    value: float
    unit: str
    user_unit: type[BaseUnit] = field(init=False)
    factor: float = field(init=False)
    display_unit: str = field(init=False)
    _unit_enum: type[BaseUnit] = field(init=False, repr=False, compare=False)
    dimension: Dimension = field(init=False, repr=False)

    def __post_init__(self):
        # Dynamic enum resolution
        if not hasattr(self.__class__, "_unit_enum"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define a class attribute '_unit_enum'"
            )
        if not hasattr(self.__class__, "dimension"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define a class attribute 'dimension'"
            )

        child_unit_class = self._unit_enum

        # Match by name or display string
        if self.unit in child_unit_class.__members__:
            parsed = child_unit_class[self.unit]
        else:
            matches = [
                unit
                for unit in child_unit_class
                if getattr(unit, "display", None) == self.unit
            ]
            if not matches:
                raise ValueError(f"Unknown unit: {self.unit} in {child_unit_class}")
            parsed = matches[0]

        object.__setattr__(self, "user_unit", parsed)
        object.__setattr__(self, "factor", getattr(parsed, "factor", parsed.value))
        object.__setattr__(
            self, "display_unit", getattr(parsed, "display", parsed.name)
        )

    def to_base_units(self) -> float:
        return self.value * self.factor

    def convert(self, dest_unit: str | BaseUnit) -> BaseMeasure:
        """
        Convert this measure to a different unit.
        """
        # 1. Resolve the destination unit to an Enum member
        target_enum = None
        enum_cls = self._unit_enum

        if isinstance(dest_unit, BaseUnit):
            target_enum = dest_unit
        elif isinstance(dest_unit, str):
            # Try finding by Name (e.g., "MPa")
            if dest_unit in enum_cls.__members__:
                target_enum = enum_cls[dest_unit]
            else:
                # Try finding by Display string (e.g., "MPa" or "N/m^2")
                for member in enum_cls:
                    if member.display == dest_unit:
                        target_enum = member
                        break

        if target_enum is None:
            raise ValueError(
                f"Unit '{dest_unit}' is not valid for {self.__class__.__name__}"
            )

        # 2. Perform Conversion
        new_value = self.value * self.factor / target_enum.factor

        # 3. Return new instance
        # We pass the display string (or name) to let __post_init__ handle the rest
        return self.__class__(new_value, target_enum.display)

    def __float__(self):
        return self.to_base_units()

    def __str__(self) -> str:
        return f"{self.value:g} {self.display_unit}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.value:g} {self.display_unit}>"

    def __format__(self, format_spec: str):
        return format(self.value, format_spec)

    def __hash__(self):
        return hash((self.to_base_units(), self._unit_enum))

    def __add__(self, other):
        if not isinstance(other, BaseMeasure):
            return NotImplemented
        if self._unit_enum is not other._unit_enum:
            raise TypeError("Cannot add different physical dimensions")

        base_sum = self.to_base_units() + other.to_base_units()
        return self.__class__(base_sum / self.factor, self.unit)

    def __sub__(self, other):
        if not isinstance(other, BaseMeasure):
            return NotImplemented
        if self._unit_enum is not other._unit_enum:
            raise TypeError("Cannot subtract different physical dimensions")

        base_diff = self.to_base_units() - other.to_base_units()
        return self.__class__(base_diff / self.factor, self.unit)

    @overload
    def __mul__(self, other: int | float) -> Self: ...

    @overload
    def __mul__(self, other: "BaseMeasure") -> Any: ...

    def __mul__(self, other):
        from units.registries import MultiplicationRegistry

        if isinstance(other, (int, float)):
            return self.__class__(self.value * other, self.unit)

        if isinstance(other, BaseMeasure):
            return MultiplicationRegistry.resolve(self, other)

        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    @overload
    def __truediv__(self, other: int | float) -> Self: ...

    @overload
    def __truediv__(self, other: "BaseMeasure") -> float | BaseMeasure: ...

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(self.value / other, self.unit)

        if isinstance(other, BaseMeasure):
            from units.registries import DivisionRegistry

            return DivisionRegistry.resolve(self, other)

        return NotImplemented

    def _cmp_value(self, other):
        if isinstance(other, BaseMeasure):
            if self._unit_enum is not other._unit_enum:
                raise TypeError("Cannot compare different physical dimensions")
            return other.to_base_units()
        return float(other)

    def __eq__(self, other):
        return self.to_base_units() == self._cmp_value(other)

    def __lt__(self, other):
        return self.to_base_units() < self._cmp_value(other)

    def __le__(self, other):
        return self.to_base_units() <= self._cmp_value(other)

    def __gt__(self, other):
        return self.to_base_units() > self._cmp_value(other)

    def __ge__(self, other):
        return self.to_base_units() >= self._cmp_value(other)
