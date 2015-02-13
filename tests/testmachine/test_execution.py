from hypothesis.testmachine import TestMachine, produces
from hypothesis import given


def assert_no_errors(result):
    assert len(result.errors) == 0, '\n'.join(e[1] for e in result.errors)


def test_can_do_normal_style_given_tests():
    class SimpleListTests(TestMachine):
        @given([int])
        def test_reverse_invariant(self, xs):
            self.assertEqual(list(reversed(xs)), xs)

    result = SimpleListTests('test_reverse_invariant').run()
    assert_no_errors(result)
    assert len(result.failures) == 1
    assert 'Lists differ' in result.failures[0][1]


def test_can_reuse_objects_for_falsification():
    class Unique(object):
        pass

    class CompositeListTests(TestMachine):
        @produces(Unique)
        def produce_a_unique(self):
            return Unique()

        @given([Unique], Unique)
        def test_not_contained_after_remove(self, xs, y):
            if y in xs:
                xs.remove(y)
            self.assertNotIn(y, xs)

    result = CompositeListTests('test_not_contained_after_remove').run()
    assert_no_errors(result)
    assert len(result.failures) == 1


def test_can_build_things_from_lists_of_things():
    class Foo(object):
        def __init__(self, children):
            self.children = tuple(children)
            if not self.children:
                self.depth = 0
            else:
                self.depth = 1 + max(c.depth for c in children)

    class NaryTreeTests(TestMachine):
        @given([Foo])
        @produces(Foo)
        def combine(self, xs):
            return Foo(xs)

        @given(Foo)
        def test_is_shallow(self, foo):
            self.assertLess(foo.depth, 3)
    result = NaryTreeTests('test_is_shallow').run()
    assert_no_errors(result)
    assert len(result.failures) == 1
