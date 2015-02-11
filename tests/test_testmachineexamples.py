# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, unicode_literals

import pytest
from tests.testmachineexamples import exiter, floats, closeable, \
    nonuniquelists, commutativeints, unbalancedtrees


@pytest.mark.parametrize(('example', 'fork'), [
    (ex, fork)
    for ex in [floats, nonuniquelists, unbalancedtrees]
    for fork in (False, True)
] + [(exiter, True)])
def test_all_examples(example, fork):
    machine = example.machine
    machine.prog_length = 100
    machine.good_enough = 5
    machine.fork = fork
    results = machine.run()
    assert results is not None
    assert len(results) > 0


@pytest.mark.parametrize(('example', 'fork'), [
    (ex, fork)
    for ex in [commutativeints, closeable]
    for fork in (False, True)
])
def test_positive_examples(example, fork):
    machine = example.machine
    machine.fork = fork
    assert machine.run() is None
