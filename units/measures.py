from dataclasses import dataclass

from units.base_models import BaseUnit, BaseMeasure
from units.dimensions import Dimension


class Scalar(float):
    pass


class Dimensionless(BaseUnit):
    NONE = ("", 1)


@dataclass(frozen=True)
class Strain(BaseMeasure):
    _unit_enum = Dimensionless
    dimension = Dimension.STRAIN


# class StrainTensor(BaseTensor):
#     @classmethod
#     def _element_type(cls):
#         return Strain


class StressUnit(BaseUnit):
    Pa = ("Pa", 1)
    kPa = ("kPa", 1e3)
    MPa = ("MPa", 1e6)
    kg_cm2 = ("kg/cm²", 98066.5)


@dataclass(frozen=True)
class Stress(BaseMeasure):
    _unit_enum = StressUnit
    dimension = Dimension.STRESS


# class StressTensor(BaseTensor):
#     @classmethod
#     def _element_type(cls):
#         return Stress


class SpecificWeightUnit(BaseUnit):
    N_m3 = ("N/m³", 1)
    kN_m3 = ("kN/m³", 1000)
    kg_m3 = ("kg/m³", 9.80665)
    kg_cm3 = ("kg/cm³", 9806650)
    g_cm3 = ("g/cm³", 9806.650)


@dataclass(frozen=True)
class SpecificWeight(BaseMeasure):
    _unit_enum = SpecificWeightUnit
    dimension = Dimension.SPECIFIC_WEIGHT


class EnergyDensityUnit(BaseUnit):
    J_m3 = ("J/m³", 1)
    Pa = ("Pa", 1)


@dataclass(frozen=True)
class EnergyDensity(BaseMeasure):
    _unit_enum = EnergyDensityUnit
    dimension = Dimension.ENERGY_DENSITY


class LengthUnit(BaseUnit):
    m = ("m", 1)
    cm = ("cm", 0.01)
    mm = ("mm", 0.001)


@dataclass(frozen=True)
class Length(BaseMeasure):
    _unit_enum = LengthUnit
    dimension = Dimension.LENGTH
