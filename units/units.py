# units/measures.py

from units.base_models import BaseMeasure, BaseUnit
from units.dimensions import Dimension


# --- Dimensions ---

# --- Dimensions ---

FORCE = Dimension(M=1, L=1, T=-2)
AREA = Dimension(L=2)
VOLUME = Dimension(L=3)
LENGTH = Dimension(L=1)

STRESS = FORCE / AREA
MOMENT = FORCE * LENGTH
DENSITY = Dimension(M=1, L=-3)
SPECIFIC_WEIGHT = FORCE / VOLUME
STRAIN = Dimension()


# --- Units ---


class ForceUnit(BaseUnit):
    N = ("N", 1)
    kN = ("kN", 1e3)


class LengthUnit(BaseUnit):
    m = ("m", 1)
    cm = ("cm", 0.01)
    mm = ("mm", 0.001)


class AreaUnit(BaseUnit):
    m2 = ("m²", 1)
    cm2 = ("cm²", 1e-4)


class VolumeUnit(BaseUnit):
    m3 = ("m³", 1)


class StressUnit(BaseUnit):
    Pa = ("Pa", 1)
    kPa = ("kPa", 1e3)
    MPa = ("MPa", 1e6)


class MomentUnit(BaseUnit):
    Nm = ("N·m", 1)
    kNm = ("kN·m", 1e3)


class DensityUnit(BaseUnit):
    kg_m3 = ("kg/m³", 1)


class SpecificWeightUnit(BaseUnit):
    N_m3 = ("N/m³", 1)
    kN_m3 = ("kN/m³", 1e3)


# --- Measures ---


class Length(BaseMeasure):
    _unit_enum = LengthUnit
    dimension = LENGTH


class Area(BaseMeasure):
    _unit_enum = AreaUnit
    dimension = AREA


class Volume(BaseMeasure):
    _unit_enum = VolumeUnit
    dimension = VOLUME


class Force(BaseMeasure):
    _unit_enum = ForceUnit
    dimension = FORCE


class Stress(BaseMeasure):
    _unit_enum = StressUnit
    dimension = STRESS


class Moment(BaseMeasure):
    _unit_enum = MomentUnit
    dimension = MOMENT


class Density(BaseMeasure):
    _unit_enum = DensityUnit
    dimension = DENSITY


class SpecificWeight(BaseMeasure):
    _unit_enum = SpecificWeightUnit
    dimension = SPECIFIC_WEIGHT


class Strain(BaseMeasure):
    dimension = STRAIN
