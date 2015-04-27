from hypothesis.internal.multifind import multifind
from hypothesis.specifiers import integers_in_range


def test_multifinds_single_elements():
    ints = integers_in_range(1, 50)
    examples = multifind({ints}, lambda x: x)
    assert examples == {
        i: {i} for i in range(1, 51)
    }


def test_multifind_pairs_of_elements():
    ints = integers_in_range(1, 20)
    examples = multifind(
        {ints}, lambda x: {frozenset([u, v]) for u in x for v in x})
    assert len(examples) >= 100
    for v in examples.values():
        assert 1 <= len(v) <= 2
