from dataclasses import dataclass
from units.base_models import BaseUnit, BaseTensor, BaseMeasure


class Unitless(BaseUnit):
    NONE = ("", 1)


@dataclass(frozen=True)
class Strain(BaseMeasure):
    _unit_enum = Unitless


class StrainTensor(BaseTensor):
    @classmethod
    def _element_type(cls):
        return Strain


class StressUnit(BaseUnit):
    Pa = ("Pa", 1)
    kPa = ("kPa", 1e3)
    MPa = ("MPa", 1e6)


@dataclass(frozen=True)
class Stress(BaseMeasure):
    _unit_enum = StressUnit


class StressTensor(BaseTensor):
    @classmethod
    def _element_type(cls):
        return Stress


class VolumetricEnergyUnit(BaseUnit):
    J_m3 = ("J/m³", 1)
    Pa = ("Pa", 1)


@dataclass(frozen=True)
class VolumetricEnergy(BaseMeasure):
    _unit_enum = VolumetricEnergyUnit
