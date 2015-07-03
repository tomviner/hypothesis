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

import hypothesis.strategies as s
from hypothesis import Settings, find, given, assume
from hypothesis.internal.bloomfilter import BloomFilter

BloomProblem = s.integers(1, 30).map(lambda x: x * 2).flatmap(
    lambda n: s.tuples(
        s.just(n), s.lists(
            s.binary(min_size=n, max_size=n), min_size=1)))


@given(BloomProblem, settings=Settings(max_examples=200))
def test_adding_an_item_to_a_bloom_makes_it_present(problem):
    n, values = problem
    bloom = BloomFilter(n)
    for v in values:
        bloom.add(v)
        assert v in bloom


@given(BloomProblem, settings=Settings(max_examples=200))
def test_cannot_easily_saturate_a_bloom_filter(problem):
    n, values = problem
    assume(len(values) <= 1000)
    bloom = BloomFilter(n)
    for v in values:
        bloom.add(v)
    find(
        s.binary(min_size=n, max_size=n), lambda b: b not in bloom,
        settings=Settings(max_shrinks=0)
    )
