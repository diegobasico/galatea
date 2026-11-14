from units.units import Stress, Length, SpecificWeight
from galatea.soil import Soil
from galatea.footings import Footing, Mat
from galatea.bearing_capacity import (
    terzaghi_bearing_capacity,
    terzaghi_factors,
    general_bearing_capacity,
    _general_factors,
    subgrade_modulus,
)

_FACTOR_SEGURIDAD = 3.0
_OUTPUT_UNITS = "kg/cm²"
_SUBGRADE_UNITS = "kg/cm³"


def main():
    soil = Soil(
        c=Stress(0.32, "kg/cm²"),
        phi=16.4,
        gamma_nat=SpecificWeight(1.859, "g/cm³"),
        gamma_sat=SpecificWeight(1.859, "g/cm³"),
        groundwater_table=Length(2.9, "m"),
    )

    zapata = Footing(
        Df=Length(1.3, "m"),
        width=Length(3, "m"),
        shape="square",
    )

    platea = Mat(
        Df=Length(1.3, "m"),
        width=Length(6, "m"),
        length=Length(6, "m"),
    )

    print("\nTerzaghi:\n" + "-" * 14)

    Nc, Nq, Ngamma = terzaghi_factors(soil.phi)
    qu = terzaghi_bearing_capacity(zapata, soil)
    q_adm = qu / _FACTOR_SEGURIDAD

    K_mod = subgrade_modulus(q_adm, Length(3, "m"))

    print(f"Nc: {Nc}, Nq: {Nq}, Ngamma: {Ngamma}")
    print(f"σ_u  : {qu.to(_OUTPUT_UNITS):.3f} {_OUTPUT_UNITS}")
    print(f"σ_adm: {q_adm.to(_OUTPUT_UNITS):.3f} {_OUTPUT_UNITS}")
    print(f"K_mod: {K_mod.to(_SUBGRADE_UNITS):.3f} {_OUTPUT_UNITS}")

    print("\nGeneral:\n" + "-" * 14)

    qu = general_bearing_capacity(platea, soil)
    q_adm = qu / _FACTOR_SEGURIDAD

    K_mod = subgrade_modulus(q_adm, Length(6, "m"))

    Nc, Nq, Ngamma = _general_factors(soil.phi)
    print(f"Nc: {Nc}, Nq: {Nq}, Ngamma: {Ngamma}")
    print(f"σ_u  : {qu.to('kg/cm²'):.3f}")
    print(f"σ_adm: {q_adm.to('kg/cm²'):.3f}")
    print(f"K_mod: {K_mod.to(_SUBGRADE_UNITS):.3f} {_OUTPUT_UNITS}")


if __name__ == "__main__":
    main()
