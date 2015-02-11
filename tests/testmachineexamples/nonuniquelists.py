# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

"""Find an example demonstrating that lists can contain the same element
multiple times.

Example output:
    t1 = 1
    t2 = [t1, t1]
    assert unique(t2)

"""

from __future__ import division, print_function, unicode_literals

from hypothesis.testmachine import TestMachine
from hypothesis.testmachine.common import ints, check, lists

machine = TestMachine()

machine.add(
    # Populate the ints varstack with integer values
    ints(),
    # Populate the intlists varstack with lists whose elements are drawn from
    # the ints varstack
    lists(source='ints', target='intlists'),
    # Check whether a list contains only unique elements. If it contains
    # duplicates raise an error.
    check(
        lambda s: len(s) == len(set(s)), argspec=('intlists',), name='unique'
    ),
)

if __name__ == '__main__':
    # Find a program that creates a list with non-unique elements.
    machine.main()
