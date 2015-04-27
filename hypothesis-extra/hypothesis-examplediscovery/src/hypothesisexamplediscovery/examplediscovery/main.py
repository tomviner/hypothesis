from hypothesis.internal.compat import text_type, binary_type
import inspect
from hypothesis.errors import InvalidArgument
from hypothesis import strategy
from hypothesis.specifiers import one_of, just
from coverage.control import coverage as Coverage
from hypothesis.internal.multifind import multifind
from hypothesis.utils.show import show
import sys
import importlib


def execute_and_report(f, args, kwargs):
    known_files = {}
    executed_features = set()
    coverage = Coverage(branch=True)
    coverage.start()
    f(*args, **kwargs)
    coverage.stop()
    coverage._harvest_data()
    for filename, arcs in coverage.data.arcs.items():
        fileid = known_files.setdefault(filename, filename)
        for a in arcs:
            executed_features.add((fileid,) + a)
    return executed_features


def all_hypothesis_tests(module):
    if isinstance(module, (text_type, binary_type)):
        module = importlib.import_module(module)
    result = {}
    for k, v in inspect.getmembers(module):
        if getattr(v, 'is_hypothesis_test', False):
            result[k] = v
    return result


def build_exploration_strategy(module):
    tests = all_hypothesis_tests(module)
    if not tests:
        raise InvalidArgument("Module %r has no tests" % (module,))
    return strategy(one_of(
        (just(k), just(v), v.given_arguments, v.given_kwargs)
        for k, v in tests.items()
    ))


def explore_strategy_for_coverage(strategy):
    return multifind(
        strategy,
        lambda x: execute_and_report(x[1].underlying_function, *x[2:])
    )


def main():
    for module in sys.argv[1:]:
        print(module)
        strategy = build_exploration_strategy(module)
        results = explore_strategy_for_coverage(strategy)
        outcomes = []
        for example in results:
            arg_bits = []
            for a in example[2]:
                arg_bits.append(show(a))
            for k, v in example[3].items():
                arg_bits.append("%s=%s" % (k, show(v)))
            outcomes.append("%s(%s)" % (example[0], ','.join(arg_bits)))
        outcomes.sort()
        for o in outcomes:
            print(o)


if __name__ == '__main__':
    main()
