# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import math

import hypothesis.strategies as s
from hypothesis import given
from hypothesis.internal.floats import ExplodedFloat

ExplodedFloatStrategy = s.builds(
    ExplodedFloat,
    negative=s.booleans(),
    exponent=s.integers(min_value=0, max_value=((1 << 11) - 1)),
    fraction=s.integers(min_value=0, max_value=((1 << 52) - 1)),
)


def test_correctly_unpacks_nan():
    assert math.isnan(
        ExplodedFloat.from_float(float('nan')).to_float()
    )


@given(s.integers())
def test_can_convert_integral_floats(i):
    f = float(i)
    exploded = ExplodedFloat.from_float(f)
    assert exploded.to_float() == f


@given(s.integers(0, (2 ** 64) - 1))
def test_converting_to_and_from_long(l):
    assert ExplodedFloat.from_long(l).to_long() == l
