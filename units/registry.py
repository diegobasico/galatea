from typing import Type
from units.base_models import BaseMeasure
from units.dimensions import Dimension


RuleKey = tuple[Dimension, Dimension]

# TODO: WRITE DIVISION REGISTRY


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

        # Result is constructed in base units
        return result_cls(base_value, result_cls._unit_enum.__members__["Pa"].display)
