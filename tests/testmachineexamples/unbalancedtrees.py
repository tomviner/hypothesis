# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

"""Example with an entirely user defined datatype. We are constructing a binary
tree and we want it to be balanced in the sense that given a split, each of the
child nodes differ in the number of nodes they contain by at most one.
Unfortunately we forgot to implement the code for doing that. Silly us. We need
testmachine to remind us of this fact.

Example output:

    t1 = Leaf()
    t2 = Leaf()
    t3 = Leaf()
    t4 = t3.join(t2)
    t5 = t4.join(t4)
    t6 = t5.join(t1)
    assert t6.balanced()

"""

from __future__ import division, print_function, unicode_literals

from hypothesis.testmachine import TestMachine
from hypothesis.testmachine.common import check, generate, operation, \
    basic_operations


# Our tree type is a classic binary tree
class Tree(object):

    def join(self, other):
        return Join(self, other)


class Leaf(Tree):

    def balanced(self):
        return True

    def __len__(self):
        return 1

    def __repr__(self):
        return 'Leaf()'


class Join(Tree):

    def __init__(self, child0, child1):
        self.child0 = child0
        self.child1 = child1

    def __repr__(self):
        return 'Join(%r, %r)' % (self.child0, self.child1)

    def __len__(self):
        return len(self.child0) + len(self.child1)

    def balanced(self):
        if not (self.child0.balanced() and self.child1.balanced()):
            return False

        return (
            (len(self.child0) <= len(self.child1) + 1) and
            (len(self.child1) <= len(self.child0) + 1)
        )


# Business as usual
machine = TestMachine()

# Because we might as well
machine.add(basic_operations('trees'))

# We can always generate leaf nodes. We ignore the Random argument we're given
# because all Leaves are created equal.
machine.add(generate(lambda _: Leaf(), 'trees'))


# Given two trees, we can join them together into a new tree
machine.add(operation(
    argspec=('trees', 'trees'),
    target='trees',
    function=lambda x, y: x.join(y),
    pattern='{0}.join({1})'
))

# Assert that our trees are balanced.
machine.add(check(
    test=lambda x: x.balanced(),
    argspec=('trees',),
    # The pattern argument controls the output formatting when emitting an
    # example. It will be formatted with the name of the variable we are
    # checking.
    pattern='assert {0}.balanced()'
))

if __name__ == '__main__':
    machine.main()
