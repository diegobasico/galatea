import numpy as np

from units import (
    StrainTensor,
    Stress,
    StressTensor,
    VolumetricEnergy,
)


# Material properties
E = Stress(30, "MPa")  # 40,000,000 Pa
nu = 0.3
sigma_c = Stress(150, "kPa")
sigma_d1 = Stress(225, "kPa")
sigma_d2 = Stress(300, "kPa")

# Stress state arrays (Principal Stresses - Vectors)
# Note: from_list will now automatically detect 'kPa' from sigma_c
sigma_1_etapa = StressTensor.from_list([sigma_c, sigma_c, sigma_c])
sigma_2_etapa = StressTensor.from_list([sigma_c + sigma_d1, sigma_c, sigma_c])
sigma_3_etapa = StressTensor.from_list(
    [sigma_c + sigma_d1 + sigma_d2, sigma_c, sigma_c]
)


def deformacion_elastica(E: Stress, nu: float, sigma: StressTensor) -> StrainTensor:
    """
    Computes principal elastic strains given principal stresses (Hooke's Law 3D).
    """
    # Get raw floats (in Pa)
    sigma_vals = sigma.data
    E_val = E.to_base_units()

    # Hooke's Law for Principal Stresses (Vectorized)
    # epsilon_i = (1/E) * [sigma_i - nu * (sum(sigma) - sigma_i)]
    sum_sigma = np.sum(sigma_vals)
    epsilon_vals = (1.0 / E_val) * (sigma_vals - nu * (sum_sigma - sigma_vals))

    # Return as StrainTensor. Unit is dimensionless ("")
    return StrainTensor.from_array(epsilon_vals, unit="")


def energia_deformacion_volumetrica(
    sigma: StressTensor, epsilon: StrainTensor
) -> VolumetricEnergy:
    """
    U = 1/2 * sum(sigma_i * epsilon_i)
    """
    if len(sigma.data) != len(epsilon.data):
        raise ValueError("Dimensions mismatch")

    sigma_vals = sigma.data  # Pa
    epsilon_vals = epsilon.data  # Dimensionless

    # Result is J/m^3 (equivalent to Pa)
    U_value = 0.5 * np.sum(sigma_vals * epsilon_vals)

    return VolumetricEnergy(U_value, "J/m³")


# --- Execution ---

epsilon_1_etapa = deformacion_elastica(E, nu, sigma_1_etapa)
epsilon_2_etapa = deformacion_elastica(E, nu, sigma_2_etapa)
epsilon_3_etapa = deformacion_elastica(E, nu, sigma_3_etapa)

U_1 = energia_deformacion_volumetrica(sigma_1_etapa, epsilon_1_etapa)
U_2 = energia_deformacion_volumetrica(sigma_2_etapa, epsilon_2_etapa)
U_3 = energia_deformacion_volumetrica(sigma_3_etapa, epsilon_3_etapa)

print(f"\nEnergy 1: {U_1}")
print(f"\nEnergy 2: {U_2}")
print(f"\nEnergy 3: {U_3}")
print("\n" + "-" * 40)


sigma_1_matrix = StressTensor.from_array(np.diag(sigma_1_etapa.data), unit="kPa")
sigma_1_matrix = sigma_1_matrix.convert("kPa")
epsilon_1_matrix = StrainTensor.from_array(np.diag(epsilon_1_etapa.data), unit="")

sigma_2_matrix = StressTensor.from_array(np.diag(sigma_2_etapa.data), unit="kPa")
sigma_2_matrix = sigma_2_matrix.convert("kPa")
epsilon_2_matrix = StrainTensor.from_array(np.diag(epsilon_2_etapa.data), unit="")

sigma_3_matrix = StressTensor.from_array(np.diag(sigma_3_etapa.data), unit="kPa")
sigma_3_matrix = sigma_3_matrix.convert("kPa")
epsilon_3_matrix = StrainTensor.from_array(np.diag(epsilon_3_etapa.data), unit="")

print(f"\nDiagonal Matrix from σ (1da etapa): {sigma_1_matrix}")
print(f"\nDiagonal Matrix from ε (1da etapa): {epsilon_1_matrix}")
print("\n" + "-" * 40)


print(f"\nDiagonal Matrix from σ (2da etapa): {sigma_2_matrix}")
print(f"\nDiagonal Matrix from ε (2da etapa): {epsilon_2_matrix}")
print("\n" + "-" * 40)


print(f"\nDiagonal Matrix from σ (3da etapa): {sigma_3_matrix}")
print(f"\nDiagonal Matrix from ε (3da etapa): {epsilon_3_matrix}")
