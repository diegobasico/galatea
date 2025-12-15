import pytest
from units.measures import Stress, Length, SpecificWeight
from units.dimensions import Dimension


def test_unit_parsing_by_name():
    s = Stress(100, "kPa")
    assert s.to_base_units() == 100_000


def test_unit_parsing_by_display():
    s = Stress(1, "MPa")
    assert s.to_base_units() == 1_000_000


def test_conversion():
    s = Stress(1000, "kPa")
    s2 = s.convert("MPa")
    assert pytest.approx(s2.value) == 1.0


def test_add_same_dimension():
    a = Length(2, "m")
    b = Length(50, "cm")
    c = a + b
    assert pytest.approx(c.value) == 2.5


def test_add_different_dimension_fails():
    with pytest.raises(TypeError):
        Stress(1, "kPa") + Length(1, "m")


def test_scalar_multiplication():
    L = Length(2, "m")
    L2 = L * 3
    assert L2.value == 6
