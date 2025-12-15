import pytest
from units.measures import Stress, Length, SpecificWeight, Strain


def test_registered_multiplication():
    γ = SpecificWeight(20, "kN/m³")
    z = Length(2, "m")

    σ = γ * z
    assert isinstance(σ, Stress)
    assert pytest.approx(σ.to_base_units()) == 40_000


def test_symmetric_multiplication():
    z = Length(2, "m")
    ε = Strain(0.01, "")

    result = z * ε
    assert isinstance(result, Length)


def test_missing_multiplication_rule():
    with pytest.raises(TypeError):
        Stress(1, "kPa") * Stress(1, "kPa")


def test_division_rule():
    σ = Stress(100, "kPa")
    z = Length(2, "m")

    γ = σ / z

    assert isinstance(γ, SpecificWeight)


def test_missing_division_rule():
    with pytest.raises(TypeError):
        Stress(1, "kPa") / Stress(1, "kPa")
