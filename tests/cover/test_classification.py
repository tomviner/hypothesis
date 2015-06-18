from __future__ import division, print_function, absolute_import, \
    unicode_literals

import hypothesis.strategies as s
from hypothesis import Settings, given, classify
from hypothesis.database import ExampleDatabase


def test_saves_minimal_example_of_label_in_database():
    @given(
        s.lists(s.booleans()),
        settings=Settings(database=ExampleDatabase()))
    def test_is_longer_than_7(xs):
        if len(xs) >= 7:
            classify("That's definitely longer than 7")
    assert not list(test_is_longer_than_7.hypothesis_storage.fetch_basic())
    test_is_longer_than_7()
    new_examples = list(test_is_longer_than_7.hypothesis_storage.fetch_basic())
    assert new_examples
    assert [False] * 7 in new_examples
