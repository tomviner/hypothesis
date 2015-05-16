# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import struct


class ExplodedFloat(object):

    def __init__(self, negative, exponent, fraction):
        self.negative = negative
        self.exponent = exponent
        self.fraction = fraction
        sign = int(negative)
        self.as_long = (sign << 63) | (exponent << 52) | fraction
        self.as_float = struct.unpack(
            b'!d', struct.pack(b'!Q', self.as_long))[0]

    def __repr__(self):
        return (
            'ExplodedFloat(negative={0:b}, '
            'exponent={1:b}, fraction={2:b}) -> {3}'
        ).format(
            self.negative, self.exponent, self.fraction, self.as_float
        )

    def __eq__(self, other):
        return (
            isinstance(other, ExplodedFloat) and
            self.negative == other.negative and
            self.exponent == other.exponent and
            self.fraction == other.fraction
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((
            self.exponent, self.negative, self.fraction
        ))

    def __trackas__(self):
        return (self.negative, self.exponent, self.fraction)

    @classmethod
    def from_float(cls, float):
        return cls.from_long(
            struct.unpack(b'!Q', struct.pack(b'!d', float))[0]
        )

    @classmethod
    def from_long(cls, as_long):
        return cls(
            negative=as_long >> 63,
            exponent=(as_long & ((2 << 63) - 1)) >> 52,
            fraction=as_long & ((1 << 52) - 1),
        )

    def to_float(self):
        return self.as_float

    def to_long(self):
        return self.as_long
