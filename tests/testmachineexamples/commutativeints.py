# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

"""This attempts to show that integer addition is not commutative. Since
integer addition is commutative, it will not have much luck.

Example output:
    Unable to find a failing program of length <= 200 after 500 iterations

"""

from __future__ import division, print_function, unicode_literals

from hypothesis.testmachine import TestMachine
from hypothesis.testmachine.common import ints, check

machine = TestMachine()

machine.add(
    ints()
)


def commutative_add(x, y):
    return x + y == y + x

machine.add(
    check(commutative_add, ('ints', 'ints'))
)

if __name__ == '__main__':
    machine.main()
