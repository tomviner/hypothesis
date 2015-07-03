import pytest

from hypothesis.internal.bitarray import BitArray
from hypothesis import given
import hypothesis.strategies as st
from hypothesis.internal.compat import hrange


@given(st.lists(st.booleans()))
def test_boolean_is_equivalent_to_a_bitarray(xs):
    arr = BitArray(len(xs))
    assert len(arr) == len(xs)
    for i in hrange(len(xs)):
        arr[i] = xs[i]

    for i in hrange(len(xs)):
        assert arr[i] == xs[i]


def test_bitarray_errors_on_out_of_bounds_access():
    x = BitArray(10)
    for i in (-2, -1, 10, 11):
        with pytest.raises(IndexError):
            x[i] = True
        with pytest.raises(IndexError):
            x[i]
