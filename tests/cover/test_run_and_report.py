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
from contextlib import contextmanager

from hypothesis.internal.coverage import run_and_report


@contextmanager
def trace(fn):
    original_trace = sys.gettrace()
    try:
        sys.settrace(fn)
        yield
    finally:
        sys.settrace(original_trace)


def test_can_run_and_report_success():
    assert run_and_report(lambda: 42)[:2] == (True, 42)


def test_can_run_and_report_errors():
    def boom():
        raise ValueError()

    x = run_and_report(boom)
    assert x[0] is False
    assert isinstance(x[1], ValueError)


def test_gives_a_stable_answer():
    def stuff():
        pass
    assert run_and_report(stuff) == run_and_report(stuff)


def test_can_distinguish_between_different_lines_hit():
    def hi(x):
        if x:
            return 0
        else:
            return 0
    u, v = run_and_report(lambda: hi(False)), run_and_report(lambda: hi(True))
    assert u[-1] != v[-1]
    assert u[:2] == v[:2]


def test_can_distinguish_between_different_branches_hit():
    def ok(t):
        y = 1
        if t:
            y = 1
        return y

    def hi(t):
        ok(True)
        ok(t)

    u, v = run_and_report(lambda: hi(False)), run_and_report(lambda: hi(True))
    assert u[-1] != v[-1]
    assert u[:2] == v[:2]


def test_calls_correct_trace_function_on_local_scope():
    lines = [0]
    bracket = [False]

    def line_trace(frame, event, arg):
        if frame.f_code.co_name == 'do_some_stuff':
            lines[0] += 1

    def call_trace(frame, event, arg):
        if event == 'call':
            return line_trace

    def do_some_stuff():
        bracket[0] = True
        x = []
        y = []
        x + y
        bracket[0] = False
        bracket[1] = lines[0]

    with trace(call_trace):
        run_and_report(do_some_stuff)
        assert lines[0] > 0
