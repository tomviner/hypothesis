# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, unicode_literals

import pytest
from hypothesis.testmachine import TestMachine
from hypothesis.testmachine.common import generate


def test_does_not_hide_error_in_generate():
    def broken(r):
        raise ValueError()

    machine = TestMachine()
    machine.add(generate(broken, 'broken'))
    with pytest.raises(ValueError):
        machine.run()
