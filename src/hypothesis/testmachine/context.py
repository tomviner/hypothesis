# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, unicode_literals

from random import Random
from collections import namedtuple, defaultdict

ProgramStep = namedtuple(
    'ProgramStep',
    ('definitions', 'arguments', 'operation')
)

Consume = namedtuple('Consume', ('varstack',))


def consume(varstack):
    return Consume(varstack)


def requirements(argspec):
    result = {}
    for x in argspec:
        if isinstance(x, Consume):
            x = x.varstack
        result[x] = result.get(x, 0) + 1
    return result


class TestMachineError(Exception):
    pass


class VarStack(object):

    def __init__(self, name, context):
        self.name = name
        self.context = context
        self.data = []

    def pop(self, i=0):
        i = -1 - i
        name, value = self.data[i]
        del self.data[i]
        self.context.on_read(name)
        return value

    def consume(self, i=0):
        i = -1 - i
        name, value = self.data[i]
        del self.data[i]
        self.context.on_read(name)
        self.data = filter(lambda (n, v): n != name, self.data)
        return value

    def push(self, head):
        v = self.context.newvar()
        self.data.append((v, head))
        self.context.on_write(v)

    def dup(self):
        self.data.append(self.data[-1])

    def swap(self):
        self.data[-1], self.data[-2] = self.data[-2], self.data[-1]

    def rot(self):
        (self.data[-1], self.data[-2], self.data[-3]) = (
            self.data[-2], self.data[-3], self.data[-1]
        )

    def peek(self, index=0):
        i = -1 - index
        name, value = self.data[i]
        self.context.on_read(name)
        return value

    def has(self, count):
        return len(self.data) >= count

    def size(self):
        return len(self.data)


class RunContext(object):

    def __init__(self, random=None, simulation=False):
        self.random = random or Random()
        self.varstacks = {}
        self.var_index = 0
        self.reset_tracking()
        self.log = []
        self.simulation = simulation

    def reset_tracking(self):
        self.values_read = []
        self.values_written = []

    def run_program(self, program):
        for operation in program:
            self.execute(operation)

    def heights(self):
        result = {}
        for k, s in self.varstacks.items():
            result[k] = s.size()
        return result

    def execute(self, operation):
        self.reset_tracking()
        try:
            if self.simulation:
                operation.simulate(self)
            else:
                operation.invoke(self)

            self.log.append(ProgramStep(
                operation=operation,
                definitions=tuple(self.values_written),
                arguments=tuple(self.values_read)
            ))
        except Exception:
            self.log.append(ProgramStep(
                operation=operation,
                definitions=(),
                arguments=tuple(self.values_read)
            ))
            raise

    def __repr__(self):
        return 'RunContext(%s)' % (
            ', '.join(
                '%s=%r' % (v.name, len(v.data))
                for v in self.varstacks.values()
            )
        )

    def newvar(self):
        self.var_index += 1
        return 't%d' % (self.var_index,)

    def on_read(self, var):
        self.values_read.append(var)

    def on_write(self, var):
        self.values_written.append(var)

    def varstack(self, name):
        if isinstance(name, Consume):
            name = name.varstack
        try:
            return self.varstacks[name]
        except KeyError:
            varstack = VarStack(name, self)
            self.varstacks[name] = varstack
            return varstack

    def read(self, argspec):
        result = []
        seen = defaultdict(lambda: 0)
        for a in argspec:
            varstack = self.varstack(a)
            if isinstance(a, Consume):
                v = varstack.consume(seen[a.varstack])
            else:
                v = varstack.peek(seen[a])
                seen[a] += 1
            result.append(v)
        return tuple(result)
