from enum import Enum, auto


class Dimension(Enum):
    LENGTH = auto()
    STRESS = auto()
    SPECIFIC_WEIGHT = auto()
    STRAIN = auto()
    ENERGY_DENSITY = auto()
