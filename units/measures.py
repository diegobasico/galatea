from dataclasses import dataclass

from units.base_models import BaseArray, BaseMeasure, BaseUnit


class Unitless(BaseUnit):
    NONE = ("", 1)


# ------------------
# Strains
# ------------------


@dataclass(frozen=True)
class Strain(BaseMeasure):
    _unit_enum = Unitless


class StrainArray(BaseArray[Strain]):
    @classmethod
    def _element_type(cls):
        return Strain


# ------------------
# Stress
# ------------------


class StressUnit(BaseUnit):
    Pa = ("Pa", 1)
    kPa = ("kPa", 1e3)
    MPa = ("MPa", 1e6)


@dataclass(frozen=True)
class Stress(BaseMeasure):
    _unit_enum = StressUnit


class StressArray(BaseArray[Stress]):
    @classmethod
    def _element_type(cls):
        return Stress


# ------------------
# Volumetric Energy
# ------------------


class VolumetricEnergyUnit(BaseUnit):
    J_m3 = ("J/m³", 1)
    Pa = ("Pa", 1)
    kPa = ("kPa", 1e3)
    MPa = ("MPa", 1e6)


@dataclass(frozen=True)
class VolumetricEnergy(BaseMeasure):
    _unit_enum = VolumetricEnergyUnit


class VolumetricEnergyArray(BaseArray[VolumetricEnergy]):
    @classmethod
    def _element_type(cls):
        return VolumetricEnergy
