from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Iterable, TypeVar, overload

import numpy as np

from units.dimensions import Dimension


T = TypeVar("T", bound="BaseTensor")


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

    def __mul__(self, other):
        from units.registry import MultiplicationRegistry

        if isinstance(other, (int, float)):
            return self.__class__(self.value * other, self.unit)

        if isinstance(other, BaseMeasure):
            return MultiplicationRegistry.resolve(self, other)

        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(self.value / other, self.unit)
        return NotImplemented

    # TODO: IMPLEMENT DIVISION BETWEEN DIFFERENT UNITS (REGISTRY)

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


@dataclass(frozen=False)
class BaseTensor:
    """
    Tensor base class.
    """

    data: np.ndarray
    unit: str | None

    def __post_init__(self):
        # 1. Store Data
        self.data = np.array(self.data, dtype=float)

        # 2. Unit Validation
        if self.unit is not None:
            elem_cls = self._element_type()
            if elem_cls is not None:
                # If this tensor enforces a specific type (e.g. Stress),
                # we must validate the unit string against that type's Enum.
                is_valid = False
                enum_cls = elem_cls._unit_enum

                # Check against Enum Names (e.g. 'MPa') and Display Values (e.g. 'J/m³')
                for member in enum_cls:
                    if member.name == self.unit or member.display == self.unit:
                        is_valid = True
                        break

                if not is_valid:
                    # Allow 'None' or empty string only if the Enum has a matching blank member
                    # (Used for dimensionless Strains)
                    if self.unit == "" and any(u.display == "" for u in enum_cls):
                        is_valid = True

                if not is_valid:
                    valid_options = [f"{u.name}('{u.display}')" for u in enum_cls]
                    raise ValueError(
                        f"Unit '{self.unit}' is invalid for {self.__class__.__name__} "
                        f"(Element: {elem_cls.__name__}).\n"
                        f"Valid options: {', '.join(valid_options)}"
                    )

    @classmethod
    def _element_type(cls) -> type[BaseMeasure] | None:
        return None

    @staticmethod
    def _to_float(x: Any) -> float:
        if hasattr(x, "to_base_units"):
            return x.to_base_units()
        if hasattr(x, "value"):
            return float(x.value)
        return float(x)

    @classmethod
    def from_array(cls: type[T], array: np.ndarray, unit=None) -> T:
        return cls(array, unit)

    @classmethod
    def from_list(cls: type[T], data: Iterable, unit=None) -> T:
        if unit is None:
            flat_data = list(data)
            first = flat_data[0]
            if isinstance(first, list):
                first = first[0]

            if hasattr(first, "display_unit"):
                unit = first.display_unit
            elif hasattr(first, "unit"):
                unit = first.unit

        cleaned_data = np.vectorize(cls._to_float)(data)
        return cls(cleaned_data, unit)

    def astype(self, dtype):
        return self.data.astype(dtype)

    def __repr__(self):
        # 1. Default to base units (factor 1.0)
        factor = 1.0

        # 2. If a unit is assigned, try to find its factor
        elem_cls = self._element_type()
        if self.unit and elem_cls and hasattr(elem_cls, "_unit_enum"):
            # Look up the unit enum wrapper
            # (Simplistic lookup by display string or name)
            for u in elem_cls._unit_enum:
                if u.display == self.unit or u.name == self.unit:
                    factor = u.factor
                    break

        # 3. Create a view of the data scaled for display
        #    (We use formatting options to keep it clean)
        display_data = self.data / factor

        # 4. Return the string representation
        return (
            f"<{self.__class__.__name__} "
            f"shape={self.data.shape} "
            f"unit='{self.unit}'>\n"
            f"{display_data}"
        )

    # -------------------------------------------------------------------------
    # TYPE HINTING OVERLOADS (The Fix)
    # -------------------------------------------------------------------------

    # Case 1: Slicing (e.g., tensor[0:2]) -> Always returns a Tensor
    @overload
    def __getitem__(self: T, item: slice | np.ndarray | list) -> T: ...

    # Case 2: Integer Indexing (e.g., tensor[0])
    # We return 'Any' here to silence the linter.
    # Technically it returns (T | BaseMeasure | float), but 'Any' allows
    # the linter to accept chain calls like tensor[0][0].
    @overload
    def __getitem__(self: BaseTensor, item: int | tuple) -> Any: ...

    # Implementation
    def __getitem__(self: T, item) -> T | BaseMeasure | float:
        result = self.data[item]

        if isinstance(result, np.ndarray):
            return self.__class__(result, self.unit)

        elem_cls = self._element_type()
        if elem_cls and self.unit:
            factor = 1.0
            if hasattr(elem_cls, "_unit_enum"):
                for u in elem_cls._unit_enum:
                    if u.display == self.unit or u.name == self.unit:
                        factor = u.factor
                        break
            return elem_cls(result / factor, self.unit)

        return float(result)

    def __setitem__(self, key: Any, value: Any) -> None:
        val_as_float = self._to_float(value)
        self.data[key] = val_as_float

    def __len__(self) -> int:
        return len(self.data)

    def convert(self: T, dest_unit: str | BaseUnit) -> T:
        """
        Return a new Tensor with the specific unit.
        Since BaseTensor stores data in Base Units (Pa), this simply
        validates the unit and updates the display context.
        """
        target_display = None

        # 1. Identify the Element Type (e.g., Stress) to check valid units
        elem_cls = self._element_type()

        if elem_cls is not None:
            enum_cls = elem_cls._unit_enum

            # Resolve Unit/String to the correct Display String
            if isinstance(dest_unit, BaseUnit):
                target_display = dest_unit.display
            elif isinstance(dest_unit, str):
                # Validate string against Enum
                if dest_unit in enum_cls.__members__:
                    target_display = enum_cls[dest_unit].display
                else:
                    for member in enum_cls:
                        if member.display == dest_unit:
                            target_display = member.display
                            break

            if target_display is None:
                raise ValueError(
                    f"Unit '{dest_unit}' is incompatible with {elem_cls.__name__}"
                )
        else:
            # Fallback for generic tensors with no strict element type
            target_display = (
                dest_unit.display if isinstance(dest_unit, BaseUnit) else dest_unit
            )

        # 2. Return a new Tensor (Data remains in Base Units, only unit label changes)
        return self.__class__(self.data, unit=target_display)
