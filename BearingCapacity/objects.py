from enum import Enum
from dataclasses import dataclass
from units.units import Stress, SpecificWeight, Length


@dataclass(frozen=True, kw_only=True)
class Foundation:
    Df: Length
    width: Length


class FoundationShape(Enum):
    square = "square"
    continuous = "continuous"
    circular = "circular"


@dataclass(frozen=True)
class Footing(Foundation):
    shape: FoundationShape | str

    def __post_init__(self):
        if isinstance(self.shape, str):
            try:
                object.__setattr__(
                    self,
                    "shape",
                    FoundationShape(self.shape),
                )
            except ValueError as e:
                raise ValueError(
                    f"Invalid foundation shape: {self.shape!r}. "
                    f"Valid values: {[s.value for s in FoundationShape]}"
                ) from e


@dataclass(frozen=True)
class Mat(Foundation):
    length: Length
    inclination: float = 0
    # inclination of load with respect to vertical
    # α is always in degrees


@dataclass(frozen=True)
class Soil:
    c: Stress
    phi: float  # φ is always in degrees
    gamma_nat: SpecificWeight
    gamma_sat: SpecificWeight
    groundwater_table: Length
