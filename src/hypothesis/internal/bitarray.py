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

from array import array


class BitArray(object):

    def __init__(self, n):
        self.length = n
        self.data = array('L')
        self.elements_per_index = self.data.itemsize * 8
        while self.elements_per_index * len(self.data) < n:
            self.data.append(0)

    def __len__(self):
        return self.length

    def __check_index(self, i):
        if i < 0 or i >= self.length:
            raise IndexError('Index %d out of range [0, %d' % (
                i, self.length
            ))

    def __getitem__(self, i):
        self.__check_index(i)
        element = self.data[i // self.elements_per_index]
        offset = i % self.elements_per_index
        return bool(element & (1 << offset))

    def __setitem__(self, i, v):
        self.__check_index(i)
        v = bool(v)
        offset = i % self.elements_per_index
        if v:
            self.data[i // self.elements_per_index] |= (1 << offset)
        else:
            self.data[i // self.elements_per_index] &= ~(1 << offset)
