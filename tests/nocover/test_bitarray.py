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

from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule
from hypothesis.strategies import booleans, integers
from hypothesis.internal.bitarray import BitArray


class MirroredBitArray(object):

    def __init__(self, n):
        self.bitarray = BitArray(n)
        self.mirror = [False] * n

    def __len__(self):
        assert len(self.mirror) == len(self.bitarray)
        return len(self.bitarray)

    def __getitem__(self, i):
        bitv = self.bitarray[i]
        mirrorv = self.mirror[i]
        assert bitv == mirrorv
        return bitv

    def __setitem__(self, i, v):
        v = bool(v)
        self.bitarray[i] = v
        self.mirror[i] = v
        assert self[i] == v


Indices = integers(0, 5000)


class BitArrayModel(RuleBasedStateMachine):
    bitarrays = Bundle('bitarrays')

    @rule(target=bitarrays, n=Indices)
    def build_array(self, n):
        return MirroredBitArray(n)

    @rule(x=bitarrays, i=Indices, v=booleans())
    def set_value(self, x, i, v):
        try:
            x[i] = v
        except IndexError:
            pass

    @rule(x=bitarrays, i=Indices)
    def get_value(self, x, i):
        try:
            x[i]
        except IndexError:
            pass

    @rule(x=bitarrays)
    def check_length(self, x):
        len(x)


TestBitArrays = BitArrayModel.TestCase
