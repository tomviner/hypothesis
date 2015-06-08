# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import sys

from hypothesis.internal.compat import hrange


def run_and_report(fn):
    with Tracer() as t:
        try:
            base = (True, fn())
        except Exception as e:
            base = (False, e)
    data = set(t.data)
    for i in hrange(len(t.data) - 1):
        data.add(tuple(t.data[i:i + 2]))
    return base + (data,)


class Tracer(object):  # pragma: no cover

    def __init__(self):
        self.files = {}

    def __enter__(self):
        self.original_gettrace = sys.gettrace()
        sys.settrace(self.trace_with(self.original_gettrace))
        self.data = set()
        return self

    def trace_with(self, original):
        if original is None:
            def accept(frame, event, arg):
                self.data.add(
                    (frame.f_lineno, frame.f_code.co_filename))
                return accept
        else:
            def accept(frame, event, arg):
                local = original(frame, event, arg)
                self.data.add(
                    (frame.f_lineno, frame.f_code.co_filename))
                return self.trace_with(local)
        return accept

    def __exit__(self, exc_type, exc_val, ex_tb):
        sys.settrace(self.original_gettrace)
        delattr(self, 'original_gettrace')
