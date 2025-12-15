from enum import Enum
from typing import Optional
from dataclasses import dataclass

import numpy as np
import polars as pl

from units.measures import Stress, SpecificWeight, Length


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

GAMMA_W = SpecificWeight(1, "g/cm³")  # Water unit weight
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
    shape: Optional[FootingShape] = None
    length: Optional[Length] = None
    inclination: Optional[float] = (
        0  # α = inclination of the load with respect to the vertical
    )


@dataclass(frozen=True)
class Soil:
    c: Stress
    phi: float  # φ is always in degrees
    gamma_nat: SpecificWeight
    gamma_sat: SpecificWeight
    groundwater_table: Length


# ------------------------------------------------------------------
# Geotechnical Functions - Corrections
# ------------------------------------------------------------------


def effective_overburden(soil: Soil, Df: Length) -> Stress:
    """
    Effective vertical stress at footing base. (Coduto, 2021)
    Returns Stress.
    """

    if soil.groundwater_table >= Df:
        return soil.gamma_nat * Df

    gamma_sub = soil.gamma_sat - GAMMA_W

    return soil.gamma_nat * soil.groundwater_table + gamma_sub * (
        Df - soil.groundwater_table
    )


def corrected_gamma_for_Ngamma(
    soil: Soil, Df: Length, B: Length, zw: Length
) -> SpecificWeight:
    gamma_sub = soil.gamma_sat - GAMMA_W

    if zw >= Df + B:
        return soil.gamma_nat

    if zw <= Df:
        return gamma_sub

    # NF entre la base y B
    return gamma_sub + (zw - Df) / B * (soil.gamma_nat - gamma_sub)


# ------------------------------------------------------------------
# Geotechnical Functions - Terzaghi
# ------------------------------------------------------------------


def local_shear_parameters(c: Stress, phi: float) -> tuple[Stress, float]:
    """
    Returns c and ɸ for local shear failure. (Terzaghi, 1943)
    """

    c = c * 2 / 3
    phi = np.degrees(np.atan(np.tan(np.radians(phi)) * 2 / 3))

    return c, phi


def terzaghi_factors(phi: float) -> tuple[float, float, float]:
    """
    Terzaghi bearing capacity factors for general shear failure. (Coduto, 2021)
    """

    if phi == 0.0:
        return 5.7, 1.0, 0.0

    phi_rad = np.radians(phi)

    a_theta = np.exp(np.pi * (0.75 - phi / 360) * np.tan(phi_rad))

    Nq = a_theta**2 / (2 * np.cos(np.radians(45) + phi_rad / 2) ** 2)
    Nc = (Nq - 1) / np.tan(phi_rad)
    Ngamma = (
        2 * (Nq + 1) * np.tan(phi_rad) / (1 + 0.4 * np.sin(4 * phi_rad))
    )  # Fitted curve by Coduto

    return Nc, Nq, Ngamma


def terzaghi_bearing_capacity(
    footing: Footing, soil: Soil, local: bool = False
) -> Stress:
    """
    Ultimate bearing capacity (Terzaghi, 1943).
    Returns Stress.
    """

    if not footing.shape:
        raise ValueError("Missing foundation shape.")

    if local:
        c, phi = local_shear_parameters(soil.c, soil.phi)
        bearing_soil = Soil(
            c,
            phi,
            gamma_nat=soil.gamma_nat,
            gamma_sat=soil.gamma_sat,
            groundwater_table=soil.groundwater_table,
        )
    else:
        bearing_soil = soil

    zw = bearing_soil.groundwater_table
    phi = bearing_soil.phi
    c = bearing_soil.c
    D = footing.Df
    B = footing.width
    gamma_corr = corrected_gamma_for_Ngamma(soil=soil, Df=D, B=B, zw=zw)

    sigma_v_eff = effective_overburden(bearing_soil, D)
    Nc, Nq, Ngamma = terzaghi_factors(phi)
    # Nc, Nq, Ngamma = Nc, Nq, 0.49  # HACK TRYING TO COMPARE WITH SOLVED MODELS
    print(f"Nc = {Nc:.2f}, Nq = {Nq:.2f}, Nγ = {Ngamma:.2f}")

    match footing.shape:
        case FootingShape.continuous:
            qu = c * Nc + sigma_v_eff * Nq + gamma_corr * footing.width * (0.5 * Ngamma)

        case FootingShape.square:
            qu = c * (1.3 * Nc) + sigma_v_eff * Nq + gamma_corr * B * (0.4 * Ngamma)

        case FootingShape.circular:
            qu = c * (1.3 * Nc) + sigma_v_eff * Nq + gamma_corr * B * (0.3 * Ngamma)

    return qu


# ------------------------------------------------------------------
# Geotechnical Functions - General (Vesić, Meyerhof)
# ------------------------------------------------------------------


def general_factors(phi: float) -> tuple[float, float, float]:
    """
    Bearing capacity factors for general shear failure. (Das, 2019)
    """

    phi_rad = np.radians(phi)

    if phi == 0:
        return 5.14, 1, 0

    Nq = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.radians(45) + phi_rad / 2) ** 2)
    Nc = (Nq - 1) / np.tan(phi_rad)
    Ngamma = 2 * (Nq + 1) * np.tan(phi_rad)

    return Nc, Nq, Ngamma


def shape_depth_inclination_factors(Nq: float, Nc: float, footing: Footing, soil: Soil):
    """
    Outputs factors for the general bearing capacity equation. (Das, 2019)
    """

    if not footing.length or footing.inclination is None:
        raise ValueError("Missing foundation length or inclination.")

    phi = soil.phi
    phi_rad = np.radians(phi)

    B = footing.width.value
    L = footing.length.value
    D = footing.Df.value
    inclination = footing.inclination

    # Shape factors (De Beer, 1970)
    S_c = 1 + (B / L) * (Nq / Nc)
    S_q = 1 + (B / L) * np.tan(phi_rad)
    S_gamma = 1 - 0.4 * (B / L)

    # Depth factors (Hansen, 1970)
    if D / B <= 1:
        k = D / B
    else:
        k = np.atan(D / B)

    D_c = 1 + 0.4 * k
    D_q = 1 + 2 * np.tan(phi_rad) * (1 - np.sin(phi_rad)) ** 2 * k
    D_gamma = 1

    # Inclination factors (Meyerhof, 1963)
    I_q = (1 - inclination / 90) ** 2
    I_c = I_q
    I_gamma = (1 - inclination / phi) ** 2

    return S_c, S_q, S_gamma, D_c, D_q, D_gamma, I_c, I_q, I_gamma


def general_bearing_capacity(
    footing: Footing,
    soil: Soil,
) -> Stress:
    """
    Ultimate bearing capacity (Das, 2019).
    Returns Stress.
    """

    zw = soil.groundwater_table
    phi = soil.phi
    c = soil.c
    D = footing.Df
    B = footing.width
    gamma_corr = corrected_gamma_for_Ngamma(soil=soil, Df=D, B=B, zw=zw)

    sigma_v_eff = effective_overburden(soil, footing.Df)
    Nc, Nq, Ngamma = general_factors(phi)
    print(f"Nc = {Nc:.2f}, Nq = {Nq:.2f}, Nγ = {Ngamma:.2f}")

    S_c, S_q, S_gamma, D_c, D_q, D_gamma, I_c, I_q, I_gamma = (
        shape_depth_inclination_factors(Nq=Nq, Nc=Nc, footing=footing, soil=soil)
    )

    print(
        f"S_c = {S_c:.2f}, S_q = {S_q:.2f}, S_γ = {S_gamma:.2f},\nD_c = {D_c:.2f}, D_q = {D_q:.2f}, D_γ = {D_gamma:.2f},\nI_c = {I_c:.2f}, I_q = {I_q:.2f}, I_γ = {I_gamma:.2f}"
    )

    qu = (
        c * (Nc * S_c * D_c * I_c)
        + sigma_v_eff * (Nq * S_q * D_q * I_q)
        + gamma_corr * B * 0.5 * (Ngamma * S_gamma * D_gamma * I_gamma)
    )

    return qu


# ------------------------------------------------------------------
# Nq, Nc, Nγ tables
# ------------------------------------------------------------------


def display_factors_table(method: str, local_shear_failure: bool = False):
    with pl.Config(set_tbl_rows=-1, set_tbl_cols=-1, set_float_precision=2):
        rows = []

        for phi in range(0, 42):
            match method, local_shear_failure:
                case "Terzaghi", True:
                    _, phi_local = local_shear_parameters(Stress(0, "kg/cm²"), phi)
                    Nc, Nq, Ng = map(float, terzaghi_factors(phi_local))
                case "Terzaghi", False:
                    Nc, Nq, Ng = map(float, terzaghi_factors(phi))
                case "General", _:
                    Nc, Nq, Ng = map(float, general_factors(phi))
                case _, _:
                    raise ValueError("Method must be Terzaghi or General.")

            rows.append(
                {
                    "phi": phi,
                    "Nc": Nc,
                    "Nq": Nq,
                    "Nγ": Ng,
                }
            )

        df = pl.DataFrame(rows)
        print(f"\nMethod: {method}\nLocal Shear Failure: {local_shear_failure}\n")
        print(df)


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------


if __name__ == "__main__":
    footing = Footing(
        Df=Length(1, "m"),
        width=Length(1, "m"),
        length=Length(1, "m"),
        shape=FootingShape.square,
    )

    soil = Soil(
        c=Stress(0.237803411379647, "kg/cm²"),
        phi=14.099078143577,
        gamma_nat=SpecificWeight(1.83146129445547, "g/cm³"),
        gamma_sat=SpecificWeight(1.61277588759615, "g/cm³"),
        groundwater_table=Length(2.90, "m"),
    )

    print("\nTerzaghi:\n" + "-" * 14)

    qu = terzaghi_bearing_capacity(footing, soil, local=True)
    q_adm = qu / FACTOR_SEGURIDAD

    print(f"σ_u  : {qu.convert('kg/cm²'):.3f}")
    print(f"σ_adm: {q_adm.convert('kg/cm²'):.3f}")

    footing = Footing(
        Df=Length(0.5, "m"),
        width=Length(6, "m"),
        length=Length(11, "m"),
        shape=FootingShape.square,
    )

    soil = Soil(
        c=Stress(0.237803411379647, "kg/cm²"),
        phi=14.099078143577,
        gamma_nat=SpecificWeight(1.83146129445547, "g/cm³"),
        gamma_sat=SpecificWeight(1.61277588759615, "g/cm³"),
        groundwater_table=Length(2.90, "m"),
    )

    print("\nGeneral:\n" + "-" * 14)

    qu = general_bearing_capacity(footing, soil)
    q_adm = qu / FACTOR_SEGURIDAD

    print(f"σ_u  : {qu.convert('kg/cm²'):.3f}")
    print(f"σ_adm: {q_adm.convert('kg/cm²'):.3f}")
