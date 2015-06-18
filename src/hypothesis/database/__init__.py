# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals


from hypothesis.searchstrategy.strategies import BadData
from hypothesis.database.formats import JSONFormat
from hypothesis.database.backend import SQLiteBackend


class Storage(object):

    """Handles saving and loading examples matching a particular specifier."""

    def __repr__(self):
        return 'Storage(%s)' % (self.specifier,)

    def __init__(
        self, backend, key, format,
        database
    ):
        self.database = database
        self.backend = backend
        self.format = format
        self.key = key

    def save(self, value, strategy):
        converted = strategy.to_basic(value)
        serialized = self.format.serialize_basic(converted)
        self.backend.save(self.key, serialized)

    def fetch_basic(self):
        for data in self.backend.fetch(self.key):
            yield self.format.deserialize_data(data)

    def fetch(self, strategy):
        templates = []
        for data in self.fetch_basic():
            try:
                templates.append(strategy.from_basic(data))
            except BadData:
                continue
        strategy.arrange(templates)
        return templates


class ExampleDatabase(object):

    """Object encapsulating all the things you need to get storage.

    Maps specifiers to storage for them.

    """

    def __repr__(self):
        return 'ExampleDatabase(%r, %r)' % (
            self.backend, self.format
        )

    def __init__(
        self,
        backend=None,
        format=None,
    ):
        self.backend = backend or SQLiteBackend()
        self.format = format or JSONFormat()
        if self.format.data_type() != self.backend.data_type():
            raise ValueError((
                'Inconsistent data types: format provides data of type %s '
                'but backend expects data of type %s' % (
                    self.format.data_type(), self.backend.data_type()
                )))

    def storage(self, key):
        """Get a storage object corresponding to this specifier."""
        return Storage(
            key=key,
            database=self,
            backend=self.backend,
            format=self.format,
        )

    def close(self):
        self.backend.close()
