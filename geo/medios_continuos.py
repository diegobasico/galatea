import numpy as np

from units import (
    Strain,
    StrainArray,
    Stress,
    StressArray,
    VolumetricEnergy,
)


# Material properties
E = Stress(40, "MPa")  # Young's modulus
nu = 0.3  # Poisson's ratio
sigma_c = Stress(-20, "kPa")  # Compressive stress
sigma_d = Stress(-30, "kPa")  # Deviatoric stress


# Stress state arrays (principal stresses)
sigma_1_etapa = StressArray([sigma_c, sigma_c, sigma_c])
sigma_2_etapa = StressArray([sigma_c + sigma_d, sigma_c, sigma_c])


def deformacion_elastica(E: Stress, nu: float, sigma: StressArray) -> StrainArray:
    """
    Computes principal elastic strains given principal stresses.
    E and sigma are Stress objects; returns StrainArray of Strain objects.
    """

    # Convert all stresses to floating values in base units (Pa)
    sigma_values = sigma.to_np_array().astype(float)
    E_value = float(E.to_base_units())  # E converted to Pa (scalar)

    # Hooke's law in principal directions
    epsilon = (1.0 / E_value) * (
        sigma_values
        - nu
        * np.array(
            [
                sigma_values[1] + sigma_values[2],
                sigma_values[2] + sigma_values[0],
                sigma_values[0] + sigma_values[1],
            ]
        )
    )

    # Return as Strain objects (dimensionless)
    return StrainArray([Strain(float(e), "") for e in epsilon])


def energia_deformacion_volumetrica(
    sigma: StressArray, epsilon: StrainArray
) -> VolumetricEnergy:
    """
    Energía de deformación por unidad de volumen:
        U = 1/2 * Σ (sigma_i * epsilon_i)

    sigma: StressArray (todas convertibles a float)
    epsilon: StrainArray (dimensionless)
    return: Stress en unidades base
    """

    if len(sigma) != len(epsilon):
        raise ValueError("sigma y epsilon deben tener la misma dimensión")

    # Convertir todo a base units
    sigma_values = sigma.to_np_array().astype(float)  # floats
    epsilon_values = np.array([float(e) for e in epsilon], dtype=float)

    # Energía (float en unidades base, ej. MPa)
    U_value = 0.5 * np.sum(sigma_values * epsilon_values)

    # Resulta en Stress pero es energía por volumen (1 kPa = 1 J/m³)
    return VolumetricEnergy(U_value, "J/m³")


epsilon_1 = deformacion_elastica(E, nu, sigma_1_etapa)
epsilon_2 = deformacion_elastica(E, nu, sigma_2_etapa)

U_1 = energia_deformacion_volumetrica(sigma_1_etapa, epsilon_1)
U_2 = energia_deformacion_volumetrica(sigma_2_etapa, epsilon_2)

print("Elastic strains:", epsilon_1)
print("Elastic strains:", epsilon_2)

print("Sigma de etapa 1:", sigma_1_etapa)
print("Sigma de etapa 2:", sigma_2_etapa)

print("Energía de deformación etapa 1:", U_1)
print("Energía de deformación etapa 2:", U_2)
