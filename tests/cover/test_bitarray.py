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
