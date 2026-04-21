from units.units import Stress, Length, SpecificWeight
from BearingCapacity.objects import Soil, Footing, Mat
from BearingCapacity.bearing_capacity import (
    terzaghi_bearing_capacity,
    general_bearing_capacity,
)

_FACTOR_SEGURIDAD = 3.0


def main():
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

    print(f"σ_u  : {qu.to('kg/cm²'):.3f}")
    print(f"σ_adm: {q_adm.to('kg/cm²'):.3f}")

    print("\nGeneral:\n" + "-" * 14)

    qu = general_bearing_capacity(test_mat, test_soil)
    q_adm = qu / _FACTOR_SEGURIDAD

    print(f"σ_u  : {qu.to('kg/cm²'):.3f}")
    print(f"σ_adm: {q_adm.to('kg/cm²'):.3f}")


if __name__ == "__main__":
    main()
