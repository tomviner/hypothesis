# coding=utf-8

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# Most of this work is copyright (C) 2013-2015 David R. MacIver
# (david@drmaciver.com), but it contains contributions by other. See
# https://github.com/DRMacIver/hypothesis/blob/master/CONTRIBUTING.rst for a
# full list of people who may hold copyright, and consult the git log if you
# need to determine who owns an individual contribution.

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import pytest
import hypothesis.strategies as st
from hypothesis import given
from hypothesis.internal.compat import hrange
from hypothesis.internal.bitarray import BitArray


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


def test_Bitarray_errors_on_non_integer_indices():
    x = BitArray(10)
    with pytest.raises(TypeError):
        x['foo']
