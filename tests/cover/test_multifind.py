from hypothesis.internal.multifind import multifind
from hypothesis.specifiers import integers_in_range
from hypothesis import assume


def sign(x):
    if x < 0:
        return -1
    if x == 0:
        return 0
    return 1


def test_multifinds_boundaries_of_zero():
    results = sorted(
        multifind(int, lambda x: [sign(x)])
    )
    assert results == [-1, 0, 1]


def test_multifinds_single_elements():
    ints = integers_in_range(1, 50)
    examples = multifind({ints}, lambda x: x)
    assert sorted(examples) == [
        {i} for i in range(1, 51)
    ]


def test_multifind_pairs_of_elements():
    ints = integers_in_range(1, 20)
    examples = multifind(
        {ints}, lambda x: {frozenset([u, v]) for u in x for v in x})
    assert len(examples) >= 100
    for v in examples:
        assert 1 <= len(v) <= 2


def test_can_assume_in_multifind():
    assert multifind(int, lambda x: assume(x < 0) and [1]) == [[-1]]
