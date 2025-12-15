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
