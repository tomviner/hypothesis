# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import time

import hypothesis.strategies as s
from hypothesis import Settings, assume
from hypothesis.core import multifind
from hypothesis.database import ExampleDatabase


def test_can_find_lists_by_length():
    assert multifind(
        s.lists(s.booleans()),
        classify=lambda xs: (min(5, len(xs)),)
    ) == [
        [False] * n
        for n in range(6)
    ]


def test_can_classify_with_assumptions():
    n = 10

    def classify(x):
        assume(len(x) <= n)
        assume(not x or sum(x) >= 1)
        return x

    values = multifind(s.lists(s.integers(0, n)), classify)
    assert values == [[]] + [[i] for i in range(1, n + 1)] + [[0, 1]]


def test_can_multifind_filtered_strategies():
    values = multifind(
        s.integers().filter(lambda x: x >= 3),
        lambda s: list(range(min(s, 10)))
    )
    assert values == list(range(3, 11))


def test_can_timeout_during_minimizing():
    def classify(ls):
        assume(len(ls) >= 50)
        return (len(set(ls)) >= 50,)
    start = time.time()
    values = multifind(
        s.lists(s.integers(min_value=0, max_value=10000)),
        classify, settings=Settings(timeout=0.5))
    run_time = time.time() - start
    assert run_time <= 1.5
    assert values


def test_does_not_produce_examples_only_satisfied_by_assume():
    def classify(l):
        assume(l > 0)
        return (1,)
    assert multifind(s.integers(), classify) == [1]


def test_produces_an_entry_for_the_empty_label():
    assert multifind(s.sets(s.booleans()), lambda x: x) == [
        set(), {False}, {True}
    ]


def test_can_use_the_database():
    def classify(ls):
        assume(len(ls) >= 50)
        return (len(set(ls)) >= 50,)
    database = ExampleDatabase()
    start = time.time()
    values = multifind(
        s.lists(s.integers(min_value=0, max_value=10000)),
        classify, settings=Settings(database=database))
    runtime = time.time() - start

    values2 = multifind(
        s.lists(s.integers(min_value=0, max_value=10000)),
        classify, settings=Settings(database=database, timeout=0.1 * runtime))

    assert values == values2
