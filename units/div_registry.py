from units.registries import DivisionRegistry
from units.measures import *

division = DivisionRegistry()

division.register(
    Stress,
    Length,
    SpecificWeight,
)

division.register(
    Stress,
    Strain,
    Stress,
)

division.register(
    Length,
    Length,
    Strain,  # dimensionless
)
