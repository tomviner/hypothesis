from hypothesis.core import time_to_call_it_a_day
from hypothesis.settings import Settings
from hypothesis.searchstrategy.strategies import BuildContext, strategy
from hypothesis.internal.examplesource import ParameterSource
from hypothesis.internal.tracker import Tracker
import time
from random import Random
from itertools import islice
from hypothesis.errors import UnsatisfiedAssumption


def multifind(specifier, classify, settings=None, random=None):
    settings = settings or Settings.default
    random = random or Random()
    search_strategy = strategy(specifier, settings)
    max_examples = settings.max_examples
    start_time = time.time()

    tracker = Tracker()
    build_context = BuildContext(random)

    parameter_source = ParameterSource(
        context=build_context, strategy=search_strategy,
        min_parameters=max(2, int(float(max_examples) / 10))
    )

    results = {}

    def incorporate(label, example):
        if label not in results:
            results[label] = example
            return True
        if search_strategy.strictly_simpler(example, results[label]):
            results[label] = example
            return True
        return False

    for parameter in islice(
        parameter_source, max_examples
    ):
        if len(tracker) >= search_strategy.size_upper_bound:
            break

        if time_to_call_it_a_day(settings, start_time):
            break

        example = search_strategy.produce_template(
            build_context, parameter
        )
        if tracker.track(example) > 1:
            parameter_source.mark_bad()
            continue
        try:
            classification = classify(search_strategy.reify(example))
        except UnsatisfiedAssumption:
            parameter_source.mark_bad()
            continue

        any_improvements = False
        for k in classification:
            if incorporate(k, example):
                any_improvements = True
        if not any_improvements:
            parameter_source.mark_bad()

    queue = list(results)
    random.shuffle(queue)
    while queue and not time_to_call_it_a_day(settings, start_time):
        target = queue.pop()
        template = results[target]
        changed = True
        while changed:
            changed = False
            for simplify in search_strategy.simplifiers(random, template):
                while True:
                    simpler = simplify(random, template)
                    for s in simpler:
                        if tracker.track(s) > 1:
                            continue
                        try:
                            labels = classify(search_strategy.reify(s))
                        except UnsatisfiedAssumption:
                            continue
                        if target in labels:
                            changed = True
                            template = s
                            results[target] = s

                        for l in labels:
                            if incorporate(l, s):
                                changed = True
                                queue.append(l)
                    else:
                        break

    output_tracker = Tracker()
    result = []
    for v in results.values():
        if output_tracker.track(v) > 1:
            continue
        result.append(search_strategy.reify(v))
    return result
