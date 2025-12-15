from units.registries import MultiplicationRegistry
from units.measures import *  # noqa: F403

registry = MultiplicationRegistry()

registry.register(
    SpecificWeight,
    Length,
    Stress,
)

registry.register(
    Length,
    Strain,
    Length,
)
