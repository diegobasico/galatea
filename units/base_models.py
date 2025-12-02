from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Generic, Iterable, TypeVar, Union, overload

import numpy as np

T = TypeVar("T")
SelfArray = TypeVar("SelfArray", bound="BaseArray")  # <- self-type


class BaseArray(Generic[T]):
    def __init__(self, array: Iterable[T]):
        self._data = np.array(list(array), dtype=object)

    @classmethod
    def _element_type(cls):
        raise NotImplementedError

    @overload
    def __getitem__(self: SelfArray, idx: int) -> T: ...
    @overload
    def __getitem__(self: SelfArray, idx: slice) -> SelfArray: ...

    def __getitem__(self: SelfArray, idx: Union[int, slice]) -> Union[T, SelfArray]:
        result = self._data[idx]

        if isinstance(idx, int):
            return result  # type: ignore[return-value]
        return self.__class__(result.tolist())  # type: ignore[return-value]

    @property
    def shape(self):
        return self._data.shape

    def reshape(self, *shape):
        new_arr = self._data.reshape(*shape)
        return self.__class__(new_arr.tolist())

    def copy(self):
        return self.__class__(self._data.copy().tolist())

    # ----------------------------
    # Representations
    # ----------------------------
    def __repr__(self):
        simple = ", ".join(str(x) for x in self._data.tolist())
        name = self.__class__.__name__
        return f"{name}([{simple}])"

    # ----------------------------
    # Vectorized helpers
    # ----------------------------
    def to_np_array(self) -> np.ndarray:
        """Convert all elements using float(x)."""
        return np.array([float(x) for x in self._data], dtype=float)

    # ----------------------------
    # Arithmetic (elementwise)
    # ----------------------------
    def _elementwise(self, other, op):
        if isinstance(other, self.__class__):
            if self.shape != other.shape:
                raise ValueError("Shape mismatch")
            data = [op(a, b) for a, b in zip(self._data, other._data)]
            return self.__class__(data)

        elif isinstance(other, self._element_type()):
            data = [op(a, other) for a in self._data]
            return self.__class__(data)

        elif isinstance(other, (int, float)):
            data = [op(a, other) for a in self._data]
            return self.__class__(data)

        raise TypeError(f"Unsupported operand type: {type(other)}")

    def __add__(self, other):
        return self._elementwise(other, lambda a, b: a + b)

    def __sub__(self, other):
        return self._elementwise(other, lambda a, b: a - b)

    def __mul__(self, other):
        return self._elementwise(other, lambda a, b: a * b)

    def __truediv__(self, other):
        return self._elementwise(other, lambda a, b: a / b)

    # ----------------------------
    # Comparisons
    # ----------------------------
    def __eq__(self, other) -> bool:
        """
        Must return bool. This checks array equality (same shape and all elements equal).
        """
        if not isinstance(other, self.__class__):
            return False
        if self.shape != other.shape:
            return False
        return all(a == b for a, b in zip(self._data.flat, other._data.flat))

    def eq_array(self, other) -> np.ndarray:
        """
        Vectorized elementwise comparison (the NumPy-style one).
        """
        if not isinstance(other, self.__class__):
            raise TypeError("Comparison only supported between arrays of same type.")
        if self.shape != other.shape:
            raise ValueError("Shape mismatch in comparison.")
        return np.array(
            [a == b for a, b in zip(self._data.flat, other._data.flat)]
        ).reshape(self.shape)

    # ----------------------------
    # Basic ndarray interface
    # ----------------------------
    #
    def __len__(self):
        return len(self._data)


@dataclass(frozen=True)
class BaseMeasure:
    value: float
    unit: str
    user_unit: Any = field(init=False)
    factor: float = field(init=False)
    display_unit: str = field(init=False)

    _unit_enum: Any = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        # Determine the unit enum class dynamically
        if not hasattr(self, "_unit_enum") or self._unit_enum is None:
            raise NotImplementedError("Subclasses must define _unit_enum")

        enum_class = self._unit_enum

        if self.unit in enum_class.__members__:
            parsed = enum_class[self.unit]
        else:
            # fallback: match display string
            matches = [
                u for u in enum_class if getattr(u, "display", None) == self.unit
            ]
            if not matches:
                raise ValueError(f"Unknown unit: {self.unit}")
            parsed = matches[0]

        object.__setattr__(self, "user_unit", parsed)
        object.__setattr__(self, "factor", getattr(parsed, "factor", parsed.value))
        object.__setattr__(
            self, "display_unit", getattr(parsed, "display", parsed.name)
        )

    # ---------------------
    # Representations
    # ---------------------
    def __str__(self) -> str:
        return f"{self.value:g} {self.display_unit}"

    def __repr__(self) -> str:
        return f"{self.value:g} {self.display_unit}"

    def __float__(self) -> float:
        return self.to_base_units()

    # ---------------------
    # Conversion
    # ---------------------
    def to_base_units(self) -> float:
        return self.value * self.factor

    def convert(self, target_unit: str | Any) -> float:
        enum_class = self._unit_enum
        if isinstance(target_unit, str):
            try:
                target_unit = enum_class[target_unit]
            except KeyError:
                raise ValueError(f"Unknown unit: {target_unit}")
        return self.to_base_units() / getattr(
            target_unit, "value", getattr(target_unit, "factor", 1)
        )

    def _coerce(self, other: Any) -> float:
        if not isinstance(other, BaseMeasure):
            raise TypeError(f"Expected same PhysicalQuantity type, got {type(other)}")
        return other.to_base_units()

    # ---------------------
    # Comparisons
    # ---------------------
    def __eq__(self, other):
        try:
            return self.to_base_units() == self._coerce(other)
        except Exception:
            return False

    def __lt__(self, other):
        return self.to_base_units() < self._coerce(other)

    def __le__(self, other):
        return self.to_base_units() <= self._coerce(other)

    def __gt__(self, other):
        return self.to_base_units() > self._coerce(other)

    def __ge__(self, other):
        return self.to_base_units() >= self._coerce(other)

    # ---------------------
    # Arithmetic
    # ---------------------
    def __add__(self, other):
        return self.__class__(
            (self.to_base_units() + self._coerce(other)) / self.factor,
            unit=self.user_unit.name,
        )

    def __sub__(self, other):
        return self.__class__(
            (self.to_base_units() - self._coerce(other)) / self.factor,
            unit=self.user_unit.name,
        )

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            raise TypeError(f"{self.__class__.__name__} can only multiply by scalar.")
        return self.__class__(self.value * scalar, unit=self.user_unit.name)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        if not isinstance(scalar, (int, float)):
            raise TypeError(f"{self.__class__.__name__} can only divide by scalar.")
        return self.__class__(self.value / scalar, unit=self.user_unit.name)


class BaseUnit(Enum):
    """
    Base class for all physical quantity units.
    Each unit must define (display: str, factor: float)
    """

    def __init__(self, display: str, factor: float):
        self.display = display
        self.factor = factor

    def __str__(self):
        return self.display
