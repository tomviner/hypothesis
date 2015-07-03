from hypothesis import given, find, assume, Settings
import hypothesis.strategies as s
from hypothesis.internal.bloomfilter import BloomFilter


BloomProblem = s.integers(1, 30).map(lambda x: x * 2).flatmap(
    lambda n: s.tuples(
        s.just(n), s.lists(
            s.binary(min_size=n, max_size=n), min_size=1)))


@given(BloomProblem, settings=Settings(max_examples=200))
def test_adding_an_item_to_a_bloom_makes_it_present(problem):
    n, values = problem
    bloom = BloomFilter(n)
    for v in values:
        bloom.add(v)
        assert v in bloom


@given(BloomProblem, settings=Settings(max_examples=200))
def test_cannot_easily_saturate_a_bloom_filter(problem):
    n, values = problem
    assume(len(values) <= 1000)
    bloom = BloomFilter(n)
    for v in values:
        bloom.add(v)
    find(
        s.binary(min_size=n, max_size=n), lambda b: b not in bloom,
        settings=Settings(max_shrinks=0)
    )
