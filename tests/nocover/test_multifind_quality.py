# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import hypothesis.strategies as s
from hypothesis import assume
from hypothesis.core import multifind
from tests.nocover.test_example_quality import \
    length_of_longest_ordered_sequence


def test_find_lists_with_sorting():
    def classify(ls):
        assume(len(ls) <= 10)
        result = []
        for i in range(length_of_longest_ordered_sequence(ls)):
            result.append(('f', i))
        ls = list(reversed(ls))
        for i in range(length_of_longest_ordered_sequence(ls)):
            result.append(('b', i))
        return result
    values = multifind(
        s.lists(s.integers()), classify
    )
    for v in values:
        for i in range(len(v) - 1):
            assert abs(v[i] - v[i + 1]) == 1
