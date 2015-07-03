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

from hypothesis.internal.compat import hrange
from hypothesis.internal.bitarray import BitArray


class BloomFilter(object):

    def __init__(self, hash_size):
        if hash_size % 2:
            raise ValueError(
                'hash size %d is not divisible by 2' % (hash_size,))
        self.hash_size = hash_size
        self.data = BitArray(2 ** 16)

    def add(self, value):
        for h in self.__value_to_hashes(value):
            self.data[h] = True

    def __contains__(self, value):
        return all(self.data[h] for h in self.__value_to_hashes(value))

    def __value_to_hashes(self, value):
        if len(value) != self.hash_size:
            raise ValueError('Invalid sized hash. Expected %d but got %d' % (
                self.hash_size, len(value)))
        for i in hrange(self.hash_size // 2):
            offset = i * 2
            hi = value[offset]
            lo = value[offset + 1]
            yield hi * 256 + lo
