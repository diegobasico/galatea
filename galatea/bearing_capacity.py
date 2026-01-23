from enum import Enum
from dataclasses import dataclass

import numpy as np
import polars as pl

from units.measures import Stress, SpecificWeight, Length


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

_GAMMA_W = SpecificWeight(1, "g/cm³")  # Water unit weight
_FACTOR_SEGURIDAD = 3.0

# ------------------------------------------------------------------
# Geometry & Soil Models
# ------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class _Foundation:
    Df: Length
    width: Length


class _FoundationShape(Enum):
    square = "square"
    continuous = "continuous"
    circular = "circular"


@dataclass(frozen=True)
class Footing(_Foundation):
    shape: _FoundationShape | str

    def __post_init__(self):
        if isinstance(self.shape, str):
            try:
                object.__setattr__(
                    self,
                    "shape",
                    _FoundationShape(self.shape),
                )
            except ValueError as e:
                raise ValueError(
                    f"Invalid foundation shape: {self.shape!r}. "
                    f"Valid values: {[s.value for s in _FoundationShape]}"
                ) from e


@dataclass(frozen=True)
class Mat(_Foundation):
    length: Length
    inclination: float = 0
    # inclination of load with respect to vertical
    # α is always in degrees


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


def _effective_overburden(soil: Soil, Df: Length) -> Stress:
    """
    Effective vertical stress at footing base. (Coduto, 2021)
    Returns Stress.
    """

    if soil.groundwater_table >= Df:
        return soil.gamma_nat * Df

    gamma_sub = soil.gamma_sat - _GAMMA_W

    return soil.gamma_nat * soil.groundwater_table + gamma_sub * (
        Df - soil.groundwater_table
    )


def _corrected_gamma_for_Ngamma(
    soil: Soil, Df: Length, B: Length, zw: Length
) -> SpecificWeight:
    gamma_sub = soil.gamma_sat - _GAMMA_W

    if zw >= Df + B:
        return soil.gamma_nat

    if zw <= Df:
        return gamma_sub

    # NF entre la base y base + B
    return gamma_sub + (zw - Df) / B * (soil.gamma_nat - gamma_sub)


# ------------------------------------------------------------------
# Geotechnical Functions - Terzaghi
# ------------------------------------------------------------------


def _local_shear_parameters(c: Stress, phi: float) -> tuple[Stress, float]:
    """
    Returns c and ɸ for local shear failure. (Terzaghi, 1943)
    """

    c = c * 2 / 3
    phi = np.degrees(np.atan(np.tan(np.radians(phi)) * 2 / 3))

    return c, phi


def _terzaghi_factors(phi: float) -> tuple[float, float, float]:
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
    foundation: Footing, soil: Soil, local: bool = False
) -> Stress:
    """
    Computes the ultimate bearing capacity using Terzaghi's formulation.

    Parameters
    ----------
    foundation : Footing
        Shallow foundation with validated shape and dimensions.
    soil : Soil
        Soil parameters at foundation level.
    local : bool, optional
        If True, applies local shear failure correction (Terzaghi, 1943).

    Returns
    -------
    Stress
        Ultimate bearing capacity (σ_u).

    Notes
    -----
    - Shape factors follow Terzaghi (1943).
    - Effective overburden stress accounts for groundwater position.
    - Assumes vertical loading and horizontal ground surface.
    """

    if local:
        c, phi = _local_shear_parameters(soil.c, soil.phi)
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
    D = foundation.Df
    B = foundation.width
    gamma_corr = _corrected_gamma_for_Ngamma(soil=soil, Df=D, B=B, zw=zw)

    sigma_v_eff = _effective_overburden(bearing_soil, D)
    Nc, Nq, Ngamma = _terzaghi_factors(phi)
    # Nc, Nq, Ngamma = Nc, Nq, 0.49  # HACK TRYING TO COMPARE WITH SOLVED MODELS
    # print(f"Nc = {Nc:.2f}, Nq = {Nq:.2f}, Nγ = {Ngamma:.2f}\n")

    match foundation.shape:
        case _FoundationShape.continuous:
            qu = c * Nc + sigma_v_eff * Nq + gamma_corr * B * (0.5 * Ngamma)

        case _FoundationShape.square:
            qu = c * (1.3 * Nc) + sigma_v_eff * Nq + gamma_corr * B * (0.4 * Ngamma)

        case _FoundationShape.circular:
            qu = c * (1.3 * Nc) + sigma_v_eff * Nq + gamma_corr * B * (0.3 * Ngamma)
        case _:
            raise ValueError(f"Unsupported foundation shape: {foundation.shape}")

    return qu


# ------------------------------------------------------------------
# Geotechnical Functions - General (Vesić, Meyerhof)
# ------------------------------------------------------------------


def _general_factors(phi: float) -> tuple[float, float, float]:
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


def _shape_depth_inclination_factors(Nq: float, Nc: float, foundation: Mat, soil: Soil):
    """
    Outputs factors for the general bearing capacity equation. (Das, 2019)
    """

    phi = soil.phi
    phi_rad = np.radians(phi)

    B = foundation.width.value
    L = foundation.length.value
    D = foundation.Df.value
    inclination = foundation.inclination

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
    foundation: Mat,
    soil: Soil,
) -> Stress:
    """
    Computes the ultimate bearing capacity using the general bearing
    capacity equation (Das, 2019).

    Parameters
    ----------
    foundation : Mat
        Rectangular foundation with finite length, width, and load inclination.
    soil : Soil
        Soil parameters at foundation level.

    Returns
    -------
    Stress
        Ultimate bearing capacity (σ_u).

    Notes
    -----
    - Includes shape, depth, and inclination factors.
    - Load inclination angle is assumed in degrees.
    - Groundwater corrections follow linear interpolation.
    """

    zw = soil.groundwater_table
    phi = soil.phi
    c = soil.c
    D = foundation.Df
    B = foundation.width
    gamma_corr = _corrected_gamma_for_Ngamma(soil=soil, Df=D, B=B, zw=zw)

    sigma_v_eff = _effective_overburden(soil, foundation.Df)
    Nc, Nq, Ngamma = _general_factors(phi)
    # print(f"Nc = {Nc:.2f}, Nq = {Nq:.2f}, Nγ = {Ngamma:.2f}\n")

    S_c, S_q, S_gamma, D_c, D_q, D_gamma, I_c, I_q, I_gamma = (
        _shape_depth_inclination_factors(
            Nq=Nq,
            Nc=Nc,
            foundation=foundation,
            soil=soil,
        )
    )

    # print(
    #     f"S_c = {S_c:.2f}, S_q = {S_q:.2f}, S_γ = {S_gamma:.2f}\n"
    #     f"D_c = {D_c:.2f}, D_q = {D_q:.2f}, D_γ = {D_gamma:.2f}\n"
    #     f"I_c = {I_c:.2f}, I_q = {I_q:.2f}, I_γ = {I_gamma:.2f}\n"
    # )

    qu = (
        c * (Nc * S_c * D_c * I_c)
        + sigma_v_eff * (Nq * S_q * D_q * I_q)
        + gamma_corr * B * 0.5 * (Ngamma * S_gamma * D_gamma * I_gamma)
    )

    return qu


# ------------------------------------------------------------------
# Nq, Nc, Nγ tables
# ------------------------------------------------------------------


def bearing_factors_table(
    method: str, local_shear_failure: bool = False
) -> pl.DataFrame:
    """
    Displays bearing capacity factors (Nc, Nq, Nγ) for φ = 0–41°.

    Parameters
    ----------
    method : str
        "Terzaghi" or "General".
    local_shear_failure : bool, optional
        Applies local shear correction (Terzaghi only).
    """

    if method not in {"Terzaghi", "General"}:
        raise ValueError("Method must be 'Terzaghi' or 'General'.")

    if method == "Terzaghi":
        if local_shear_failure:

            def factors(phi: float):
                _, phi_local = _local_shear_parameters(Stress(0, "kg/cm²"), phi)
                return _terzaghi_factors(phi_local)
        else:

            def factors(phi: float):
                return _terzaghi_factors(phi)
    else:

        def factors(phi: float):
            return _general_factors(phi)

    rows = []

    for phi in range(0, 42):
        Nc, Nq, Ngamma = map(float, factors(phi))
        rows.append(
            {
                "phi": phi,
                "Nc": Nc,
                "Nq": Nq,
                "Nγ": Ngamma,
            }
        )

    with pl.Config(set_tbl_rows=-1, set_tbl_cols=-1, set_float_precision=2):
        df = pl.DataFrame(rows)
        return df


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------


if __name__ == "__main__":
    test_soil = Soil(
        c=Stress(0.237803411379647, "kg/cm²"),
        phi=14.099078143577,
        gamma_nat=SpecificWeight(1.83146129445547, "g/cm³"),
        gamma_sat=SpecificWeight(1.61277588759615, "g/cm³"),
        groundwater_table=Length(2.90, "m"),
    )

    test_footing = Footing(
        Df=Length(1, "m"),
        width=Length(1, "m"),
        shape="square",
    )

    test_mat = Mat(
        Df=Length(0.5, "m"),
        width=Length(6, "m"),
        length=Length(11, "m"),
    )

    print("\nTerzaghi:\n" + "-" * 14)

    qu = terzaghi_bearing_capacity(test_footing, test_soil, local=True)
    q_adm = qu / _FACTOR_SEGURIDAD

    print(f"σ_u  : {qu.convert('kg/cm²'):.3f}")
    print(f"σ_adm: {q_adm.convert('kg/cm²'):.3f}")

    print("\nGeneral:\n" + "-" * 14)

    qu = general_bearing_capacity(test_mat, test_soil)
    q_adm = qu / _FACTOR_SEGURIDAD

    print(f"σ_u  : {qu.convert('kg/cm²'):.3f}")
    print(f"σ_adm: {q_adm.convert('kg/cm²'):.3f}")
