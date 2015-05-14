from __future__ import division, print_function, absolute_import, \
    unicode_literals

from hypothesis.extra.pytest.fixtures import fixture
from hypothesis.strategies import lists, integers


def test_basic_fixture():
    f = fixture(integers())
    assert f() == 0
    assert f() == 0


def test_constrained_fixture():
    f = fixture(lists(integers()), lambda x: sum(x) >= 1001)
    assert sum(f()) == 1001
    assert f() == f()
    assert f() is not f()
    assert False


some_list = fixture(
    lists(integers()), lambda xs: len(xs) >= 10 and sum(xs) >= 100)

some_other_list = fixture(
    lists(integers()), lambda xs: xs != sorted(xs)
)


def test_using_a_fixture(some_list):
    assert len(some_list) == 10
    assert sum(some_list) == 100


def test_using_another_fixture(some_other_list):
    assert len(some_other_list) == 2
    assert some_other_list[0] == 1 + some_other_list[1]
