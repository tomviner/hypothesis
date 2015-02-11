# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

"""
Demonstration that testmachine supports programs where the error causes the
whole program to exit. Must be run with --fork

Example output:
    die()
"""

from __future__ import division, print_function, unicode_literals

import os
import traceback

from hypothesis.testmachine import TestMachine
from hypothesis.testmachine.common import operation

machine = TestMachine()


def die():
    traceback.print_stack()
    os._exit(1)


machine.add(
    operation(die, argspec=())
)

if __name__ == '__main__':
    machine.fork = True
    machine.main()
