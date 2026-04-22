from units.units import Stress, Length, SpecificWeight
from galatea.soil import Soil
from galatea.footings import Footing, Mat
from galatea.bearing_capacity import (
    terzaghi_bearing_capacity,
    terzaghi_factors,
    general_bearing_capacity,
)

_FACTOR_SEGURIDAD = 3.0
_OUTPUT_UNITS = "kg/cm²"


def main():
    soil = Soil(
        c=Stress(0.23, "kg/cm²"),
        phi=12,
        gamma_nat=SpecificWeight(1560, "kg/m³"),
        gamma_sat=SpecificWeight(1560, "kg/m³"),
        groundwater_table=Length(1000, "m"),
    )

    zapata = Footing(
        Df=Length(3, "m"),
        width=Length(3, "m"),
        shape="square",
    )

    # platea = Mat(
    #     Df=Length(0.5, "m"),
    #     width=Length(6, "m"),
    #     length=Length(11, "m"),
    # )

    print("\nTerzaghi:\n" + "-" * 14)

    Nc, Nq, Ngamma = terzaghi_factors(soil.phi)
    qu = terzaghi_bearing_capacity(zapata, soil, local_shear_failure=False)
    q_adm = qu / _FACTOR_SEGURIDAD

    print(f"Nc: {Nc}, Nq: {Nq}, Ngamma: {Ngamma}")
    print(f"σ_u  : {qu.to(_OUTPUT_UNITS):.3f} {_OUTPUT_UNITS}")
    print(f"σ_adm: {q_adm.to(_OUTPUT_UNITS):.3f} {_OUTPUT_UNITS}")

    # print("\nGeneral:\n" + "-" * 14)

    # qu = general_bearing_capacity(platea, test_soil)
    # q_adm = qu / _FACTOR_SEGURIDAD
    #
    # print(f"σ_u  : {qu.to('kg/cm²'):.3f}")
    # print(f"σ_adm: {q_adm.to('kg/cm²'):.3f}")


if __name__ == "__main__":
    main()
