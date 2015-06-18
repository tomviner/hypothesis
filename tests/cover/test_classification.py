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
from hypothesis import Settings, given, classify
from hypothesis.database import ExampleDatabase


def test_saves_minimal_example_of_label_in_database():
    @given(
        s.lists(s.booleans()),
        settings=Settings(database=ExampleDatabase()))
    def test_is_longer_than_7(xs):
        if len(xs) >= 7:
            classify("That's definitely longer than 7")
    assert not list(test_is_longer_than_7.hypothesis_storage.fetch_basic())
    test_is_longer_than_7()
    new_examples = list(test_is_longer_than_7.hypothesis_storage.fetch_basic())
    assert new_examples
    assert [[], [[0, 0, 0, 0, 0, 0, 0]]] in new_examples
