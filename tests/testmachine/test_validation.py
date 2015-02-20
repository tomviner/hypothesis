from hypothesis.testmachine import TestMachine, ValidationError, produces
from hypothesis import given
import pytest


def test_simple_test_passes_validation():
    class CommutativeInts(TestMachine):
        @given(int, int)
        def test_commutative_add(self, x, y):
            assert x + y == y + x
    CommutativeInts().validate()


def test_fails_validation_if_no_production_rules():
    class Foo(object):
        pass

    class TestFoos(TestMachine):
        @given(Foo)
        def test_foo_is_foo(self, foo):
            pass

    with pytest.raises(ValidationError):
        TestFoos().validate()


def test_passes_validation_if_can_produce_indirectly():
    class Foo(object):
        pass

    class TestFoos(TestMachine):
        @given(int)
        @produces(Foo)
        def int_to_foo(self, i):
            return Foo()

        @given(Foo)
        def test_foo_is_foo(self, foo):
            pass

    TestFoos().validate()


def test_passes_validation_if_relevant_rules_added_explicitly():
    class Foo(object):
        pass

    class TestFoos(TestMachine):

        @given(Foo)
        def test_foo_is_foo(self, foo):
            pass

    @given(int)
    @produces(Foo)
    def int_to_foo(i):
        return Foo()

    TestFoos.add_rule(int_to_foo)

    TestFoos().validate()


def test_passes_validation_if_produces_from_several():
    class Foo(object):
        pass

    class TestFoos(TestMachine):
        @given(int)
        @produces(Foo, str)
        def int_to_foo(self, i):
            return Foo(), "hi"

        @given(Foo)
        def test_foo_is_foo(self, foo):
            pass

    TestFoos().validate()


def test_can_put_given_and_produces_in_other_order():
    class Foo(object):
        pass

    class TestFoos(TestMachine):
        @produces(Foo)
        @given(int)
        def int_to_foo(self, i):
            return Foo()

        @given(Foo)
        def test_foo_is_foo(self, foo):
            pass

    TestFoos().validate()
