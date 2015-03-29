# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import os
import sys
import subprocess

from hypothesis import given


@given(str)
def test_exact_details_irrelevant(s):
    """
    Just here to ensure that there's a @given call
    """
    pass


def test_sys_path():
    assert all(isinstance(s, str) for s in sys.path)


def test_pathsep():
    assert isinstance(os.pathsep, str)


def test_subprocess():
    """Check that Hypothesis's path changes haven't broken the ability to us it
    in the env of a subprocess."""
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(sys.path)
    subprocess.check_call(['python', '--version'], env=env)
