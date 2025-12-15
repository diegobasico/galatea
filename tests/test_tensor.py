# from units.measures import StressTensor, Stress
#
#
# def test_tensor_stores_base_units():
#     t = StressTensor([[100, 200]], "kPa")
#     assert t.data[0, 0] == 100_000
#     assert t.data[0, 1] == 200_000
#
#
# def test_tensor_element_returns_measure():
#     t = StressTensor([[100, 200]], "kPa")
#     e = t[0, 1]
#
#     assert isinstance(e, Stress)
#     assert e.value == 200
#     assert e.unit == "kPa"
#
#
# def test_tensor_conversion_preserves_base_units():
#     t = StressTensor([[1000]], "kPa")  # 1e6 Pa
#     t2 = t.convert("MPa")
#
#     assert t2.unit == "MPa"
#     assert t2.data[0, 0] == 1_000_000
#
#
# def test_tensor_slice():
#     t = StressTensor([[100, 200]], "kPa")
#     sub = t[:, 0]
#
#     assert isinstance(sub, StressTensor)
#     assert sub.data[0] == 100_000
pass
