from typing import Type
from units.base_models import BaseMeasure
from units.dimensions import Dimension


RuleKey = tuple[Dimension, Dimension]


class MultiplicationRegistry:
    _rules: dict[RuleKey, Type[BaseMeasure]] = {}

    @classmethod
    def register(
        cls,
        left: Type[BaseMeasure],
        right: Type[BaseMeasure],
        result: Type[BaseMeasure],
        symmetric: bool = True,
    ):
        """
        Declare that:
            left × right → result

        Base-unit multiplication is handled automatically.
        """

        key = (left.dimension, right.dimension)
        cls._rules[key] = result

        if symmetric:
            cls._rules[(right.dimension, left.dimension)] = result

    @classmethod
    def resolve(cls, a: BaseMeasure, b: BaseMeasure) -> BaseMeasure:
        key = (a.dimension, b.dimension)

        if key not in cls._rules:
            raise TypeError(
                f"No multiplication rule for {a.dimension.name} × {b.dimension.name}"
            )

        result_cls = cls._rules[key]

        base_value = a.to_base_units() * b.to_base_units()

        base_unit = next(iter(result_cls._unit_enum)).display
        return result_cls(base_value, base_unit)


class DivisionRegistry:
    _rules: dict[RuleKey, Type[BaseMeasure]] = {}

    @classmethod
    def register(
        cls,
        numerator: Type[BaseMeasure],
        denominator: Type[BaseMeasure],
        result: Type[BaseMeasure],
    ):
        """
        Declare that:
            numerator ÷ denominator → result
        """
        key = (numerator.dimension, denominator.dimension)
        cls._rules[key] = result

    @classmethod
    def resolve(cls, a: BaseMeasure, b: BaseMeasure) -> BaseMeasure:
        key = (a.dimension, b.dimension)

        if key not in cls._rules:
            raise TypeError(
                f"No division rule for {a.dimension.name} ÷ {b.dimension.name}"
            )

        result_cls = cls._rules[key]

        base_value = a.to_base_units() / b.to_base_units()

        # Construct result in BASE units, no hardcoding
        base_unit = next(iter(result_cls._unit_enum)).display

        return result_cls(base_value, base_unit)
