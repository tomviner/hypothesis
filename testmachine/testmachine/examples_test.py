import pytest
from .examples import (
    commutativeints, floats, nonuniquelists, unbalancedtrees, exiter, closeable
)


@pytest.mark.parametrize(("example", "fork"), [
    (ex, fork)
    for ex in [floats, nonuniquelists, unbalancedtrees]
    for fork in (False, True)
] + [(exiter, True)])
def test_all_examples(example, fork):
    machine = example.machine
    machine.prog_length = 100
    machine.good_enough = 5
    machine.fork = fork
    results = machine.run()
    assert results is not None
    assert len(results) > 0


@pytest.mark.parametrize(("example", "fork"), [
    (ex, fork)
    for ex in [commutativeints, closeable]
    for fork in (False, True)
])
def test_positive_examples(example, fork):
    machine = example.machine
    machine.fork = fork
    assert machine.run() is None
