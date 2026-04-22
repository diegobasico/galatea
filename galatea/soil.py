from dataclasses import dataclass
from units.units import Stress, SpecificWeight, Length


@dataclass(frozen=True)
class Soil:
    c: Stress
    phi: float  # φ is always in degrees
    gamma_nat: SpecificWeight
    gamma_sat: SpecificWeight
    groundwater_table: Length
