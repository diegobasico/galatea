import numpy as np
from enum import Enum
from dataclasses import dataclass

from units.measures import Stress, SpecificWeight, Length


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

GAMMA_W = SpecificWeight(9.81, "kN/m³")  # Water unit weight
FACTOR_SEGURIDAD = 3.0

# ------------------------------------------------------------------
# Geometry & Soil Models
# ------------------------------------------------------------------


class FootingShape(Enum):
    square = "square"
    continuous = "continuous"
    circular = "circular"


@dataclass(frozen=True)
class Footing:
    Df: Length
    width: Length
    shape: FootingShape


@dataclass(frozen=True)
class Soil:
    c: Stress
    phi: float  # degrees
    gamma_nat: SpecificWeight
    gamma_sat: SpecificWeight
    groundwater_table: Length


# ------------------------------------------------------------------
# Geotechnical Functions
# ------------------------------------------------------------------


def effective_overburden(soil: Soil, Df: Length) -> Stress:
    """
    Effective vertical stress at footing base.
    Returns Stress.
    """

    if soil.groundwater_table >= Df:
        return soil.gamma_nat * Df

    gamma_sub = soil.gamma_sat - GAMMA_W

    return soil.gamma_nat * soil.groundwater_table + gamma_sub * (
        Df - soil.groundwater_table
    )


def terzaghi_factors(phi: float) -> tuple[float, float, float]:
    """
    Terzaghi bearing capacity factors (phi in degrees)
    """

    if phi == 0.0:
        return 5.7, 1.0, 0.0

    phi_rad = np.radians(phi)

    a_theta = np.exp(np.pi * (0.75 - phi / 360) * np.tan(phi_rad))

    Nq = a_theta**2 / (2 * np.cos(np.radians(45) + phi_rad / 2) ** 2)
    Nc = (Nq - 1) / np.tan(phi_rad)
    Ngamma = 2 * (Nq + 1) * np.tan(phi_rad) / (1 + 0.4 * np.sin(4 * phi_rad))

    return Nc, Nq, Ngamma


def vesic_factors(phi: float) -> tuple[float, float, float]:
    """
    Vesić bearing capacity factors (phi in degrees)
    """

    if phi == 0.0:
        return 5.14, 1.0, 0.0

    phi_rad = np.radians(phi)

    Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.radians(45) + phi_rad / 2) ** 2)
    Nc = (Nq - 1) / np.tan(phi_rad)
    Ngamma = 2 * (Nq + 1) * np.tan(phi_rad)

    return Nc, Nq, Ngamma


def terzaghi_bearing_capacity(
    footing: Footing,
    soil: Soil,
) -> Stress:
    """
    Ultimate bearing capacity (Terzaghi).
    Returns Stress.
    """

    sigma_v_eff = effective_overburden(soil, footing.Df)
    Nc, Nq, Ngamma = terzaghi_factors(soil.phi)
    print(f"Nc = {Nc}, Nq = {Nq}, Nγ = {Ngamma}")

    match footing.shape:
        case FootingShape.continuous:
            qu = (
                soil.c * Nc
                + sigma_v_eff * Nq
                + soil.gamma_nat * footing.width * (0.5 * Ngamma)
            )

        case FootingShape.square:
            qu = (
                soil.c * (1.3 * Nc)
                + sigma_v_eff * Nq
                + soil.gamma_nat * footing.width * (0.4 * Ngamma)
            )

        case FootingShape.circular:
            qu = (
                soil.c * (1.3 * Nc)
                + sigma_v_eff * Nq
                + soil.gamma_nat * footing.width * (0.3 * Ngamma)
            )

        case _:
            raise ValueError("Unsupported footing shape")

    return qu


def vesic_bearing_capacity(
    footing: Footing,
    soil: Soil,
) -> Stress:
    """
    Ultimate bearing capacity (Vesić).
    Returns Stress.
    """

    sigma_v_eff = effective_overburden(soil, footing.Df)
    Nc, Nq, Ngamma = vesic_factors(soil.phi)
    print(f"Nc = {Nc}, Nq = {Nq}, Nγ = {Ngamma}")

    match footing.shape:
        case FootingShape.continuous:
            sc, sq, sg = 1.0, 1.0, 1.0

        case FootingShape.square:
            sc, sq, sg = 1.3, 1.2, 0.8

        case FootingShape.circular:
            sc, sq, sg = 1.3, 1.2, 0.6

        case _:
            raise ValueError("Unsupported footing shape")

    qu = (
        soil.c * (Nc * sc)
        + sigma_v_eff * (Nq * sq)
        + soil.gamma_nat * footing.width * (0.5 * Ngamma * sg)
    )

    return qu


################################################
"""
Sanity check:

Terzaghi      Vesić
_________     _________
φ  = 30°      φ  = 30°
Nc ≈ 37.2     Nc ≈ 30.1
Nq ≈ 22.5     Nq ≈ 18.4
Nγ ≈ 20.1     Nγ ≈ 22.4
"""
################################################


if __name__ == "__main__":
    footing = Footing(
        Df=Length(1, "m"),
        width=Length(1, "m"),
        shape=FootingShape.square,
    )

    soil = Soil(
        c=Stress(0.23, "kg/cm²"),
        phi=16.30,
        gamma_nat=SpecificWeight(1.785, "g/cm³"),
        gamma_sat=SpecificWeight(1.589, "g/cm³"),
        groundwater_table=Length(2.90, "m"),
    )

    print("\nTerzaghi:\n" + "-" * 14)

    qu = terzaghi_bearing_capacity(footing, soil)
    q_adm = qu / FACTOR_SEGURIDAD

    print(f"σ_u  : {qu.convert('kg/cm²')}")
    print(f"σ_adm: {q_adm.convert('kg/cm²')}")

    print("\nVesić:\n" + "-" * 14)

    qu = vesic_bearing_capacity(footing, soil)
    q_adm = qu / FACTOR_SEGURIDAD

    print(f"σ_u  : {qu.convert('kg/cm²')}")
    print(f"σ_adm: {q_adm.convert('kg/cm²')}")
