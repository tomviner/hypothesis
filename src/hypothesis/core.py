# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

"""This module provides the core primitives of Hypothesis, assume and given."""

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import time
import inspect
import binascii
import functools
import traceback
from random import Random
from itertools import islice
from collections import Counter, namedtuple

import hypothesis.strategies as sd
from hypothesis.extra import load_entry_points
from hypothesis.errors import Flaky, Timeout, NoSuchExample, \
    Unsatisfiable, InvalidArgument, UnsatisfiedAssumption, \
    DefinitelyNoSuchExample
from hypothesis.control import assume
from hypothesis.classify import use_classifier
from hypothesis.settings import Settings, Verbosity
from hypothesis.executors import executor
from hypothesis.reporting import report, debug_report, verbose_report, \
    current_verbosity
from hypothesis.deprecation import note_deprecation
from hypothesis.internal.tracker import Tracker
from hypothesis.internal.reflection import arg_string, copy_argspec, \
    function_digest, fully_qualified_name, \
    get_pretty_function_description
from hypothesis.internal.examplesource import ParameterSource
from hypothesis.searchstrategy.strategies import strategy

[assume]


def time_to_call_it_a_day(timeout, start_time):
    """Have we exceeded our timeout?"""
    if timeout <= 0:
        return False
    return time.time() >= start_time + timeout


def find_satisfying_template(
    search_strategy, random, condition, tracker, settings, storage=None,
    max_parameter_tries=None,
):
    """Attempt to find a template for search_strategy such that condition is
    truthy.

    Exceptions other than UnsatisfiedAssumption will be immediately propagated.
    UnsatisfiedAssumption will indicate that similar examples should be avoided
    in future.

    Returns such a template as soon as it is found, otherwise stops after
    settings.max_examples examples have been considered or settings.timeout
    seconds have passed (if settings.timeout > 0).

    May raise a variety of exceptions depending on exact circumstances, but
    these will all subclass either Unsatisfiable (to indicate not enough
    examples were found which did not raise UnsatisfiedAssumption to consider
    this a valid test) or NoSuchExample (to indicate that this probably means
    that condition is true with very high probability).

    """
    satisfying_examples = 0
    examples_considered = 0
    timed_out = False
    max_iterations = max(settings.max_iterations, settings.max_examples)
    max_examples = min(max_iterations, settings.max_examples)
    min_satisfying_examples = min(
        settings.min_satisfying_examples,
        max_examples,
    )
    start_time = time.time()

    if storage:
        for example in storage.fetch(search_strategy):
            if examples_considered >= max_iterations:
                break
            examples_considered += 1
            if time_to_call_it_a_day(settings.timeout, start_time):
                break
            tracker.track(example)
            try:
                if condition(example):
                    return example
                satisfying_examples += 1
            except UnsatisfiedAssumption:
                pass
            if satisfying_examples >= max_examples:
                break

    parameter_source = ParameterSource(
        random=random, strategy=search_strategy,
        max_tries=max_parameter_tries,
    )

    for parameter in parameter_source:  # pragma: no branch
        if len(tracker) >= search_strategy.template_upper_bound:
            break
        if examples_considered >= max_iterations:
            break
        if satisfying_examples >= max_examples:
            break
        if time_to_call_it_a_day(settings.timeout, start_time):
            break
        examples_considered += 1

        example = search_strategy.draw_template(
            random, parameter
        )
        if tracker.track(example) > 1:
            debug_report('Skipping duplicate example')
            parameter_source.mark_bad()
            continue
        try:
            if condition(example):
                return example
        except UnsatisfiedAssumption:
            parameter_source.mark_bad()
            continue
        satisfying_examples += 1
    run_time = time.time() - start_time
    timed_out = settings.timeout >= 0 and run_time >= settings.timeout
    if (
        satisfying_examples and
        len(tracker) >= search_strategy.template_upper_bound
    ):
        raise DefinitelyNoSuchExample(
            get_pretty_function_description(condition),
            satisfying_examples,
        )
    elif satisfying_examples < min_satisfying_examples:
        if timed_out:
            raise Timeout((
                'Ran out of time before finding a satisfying example for %s.' +
                ' Only found %d examples (%d satisfying assumptions) in %.2fs.'
            ) % (
                get_pretty_function_description(condition),
                len(tracker), satisfying_examples, run_time
            ))
        else:
            raise Unsatisfiable((
                'Unable to satisfy assumptions of hypothesis %s. ' +
                'Only %d out of %d examples considered satisfied assumptions'
            ) % (
                get_pretty_function_description(condition),
                satisfying_examples, len(tracker)))
    else:
        raise NoSuchExample(get_pretty_function_description(condition))


def simplify_template_such_that(
    search_strategy, random, t, f, tracker, settings, start_time
):
    """Perform a greedy search to produce a "simplest" version of a template
    that satisfies some predicate.

    Care is taken to avoid cycles in simplify.

    f should produce the same result deterministically. This function may
    raise an error given f such that f(t) returns False sometimes and True
    some other times.

    If f throws UnsatisfiedAssumption this will be treated the same as if
    it returned False.

    """
    assert isinstance(random, Random)

    yield t
    successful_shrinks = 0

    changed = True
    max_warmup = 5
    warmup = 0
    while (
        (changed or warmup < max_warmup) and
        successful_shrinks < settings.max_shrinks
    ):
        changed = False
        warmup += 1
        if warmup < max_warmup:
            debug_report('Running warmup simplification round %d' % (
                warmup
            ))
        elif warmup == max_warmup:
            debug_report('Warmup is done. Moving on to fully simplifying')

        for simplify in search_strategy.simplifiers(random, t):
            debug_report('Applying simplification pass %s' % (
                simplify.__name__,
            ))
            while True:
                simpler = simplify(random, t)
                if warmup < max_warmup:
                    simpler = islice(simpler, warmup)
                for s in simpler:
                    if time_to_call_it_a_day(settings.timeout, start_time):
                        return
                    if tracker.track(s) > 1:
                        continue
                    try:
                        if f(s):
                            successful_shrinks += 1
                            changed = True
                            yield s
                            t = s
                            break
                    except UnsatisfiedAssumption:
                        pass
                else:
                    break

            if successful_shrinks >= settings.max_shrinks:
                break


def best_satisfying_template(
    search_strategy, random, condition, settings, storage, tracker=None,
    max_parameter_tries=None,
):
    """Find and then minimize a satisfying template.

    First look in storage if it is not None, then attempt to generate
    one. May throw all the exceptions of find_satisfying_template. Once
    an example has been found it will be further minimized.

    """
    if tracker is None:
        tracker = Tracker()
    start_time = time.time()

    successful_shrinks = -1
    with settings:
        satisfying_example = find_satisfying_template(
            search_strategy, random, condition, tracker, settings, storage,
            max_parameter_tries=max_parameter_tries,
        )
        for simpler in simplify_template_such_that(
            search_strategy, random, satisfying_example, condition, tracker,
            settings, start_time,
        ):
            successful_shrinks += 1
            satisfying_example = simpler
        if storage is not None:
            storage.save(satisfying_example, search_strategy)
        if not successful_shrinks:
            verbose_report('Could not shrink example')
        elif successful_shrinks == 1:
            verbose_report('Successfully shrunk example once')
        else:
            verbose_report(
                'Successfully shrunk example %d times' % (successful_shrinks,))
        return satisfying_example


def test_is_flaky(test):
    @functools.wraps(test)
    def test_or_flaky(*args, **kwargs):
        raise Flaky(
            (
                'Hypothesis %r produces unreliable results: %r falsified it on'
                ' the first call but did not on a subsequent one'
            ) % (get_pretty_function_description(test), example))
    return test_or_flaky


HypothesisProvided = namedtuple('HypothesisProvided', ('value,'))

Example = namedtuple('Example', ('args', 'kwargs'))


def example(*args, **kwargs):
    """Add an explicit example called with these args and kwargs to the
    test."""
    if args and kwargs:
        raise InvalidArgument(
            'Cannot mix positional and keyword arguments for examples'
        )
    if not (args or kwargs):
        raise InvalidArgument(
            'An example must provide at least one argument'
        )

    def accept(test):
        if not hasattr(test, 'hypothesis_explicit_examples'):
            test.hypothesis_explicit_examples = []
        test.hypothesis_explicit_examples.append(Example(tuple(args), kwargs))
        return test
    return accept


def reify_and_execute(
    search_strategy, template, test,
    print_example=False, always_print=False,
):
    def run():
        args, kwargs = search_strategy.reify(template)
        if print_example:
            report(
                lambda: 'Falsifying example: %s(%s)' % (
                    test.__name__,
                    arg_string(
                        test, args, kwargs
                    )
                )
            )
        elif current_verbosity() >= Verbosity.verbose or always_print:
            report(
                lambda: 'Trying example: %s(%s)' % (
                    test.__name__,
                    arg_string(
                        test, args, kwargs
                    )
                )
            )
        return test(*args, **kwargs)
    return run


TestFailure = namedtuple('TestFailure', ('type',))
UserClassification = namedtuple('UserClassification', ('label',))


def given(*generator_arguments, **generator_kwargs):
    """A decorator for turning a test function that accepts arguments into a
    randomized test.

    This is the main entry point to Hypothesis. See the full tutorial
    for details of its behaviour.

    """

    # Keyword only arguments but actually supported in the full range of
    # pythons Hypothesis handles. pop so we don't later pick these up as
    # if they were keyword specifiers for data to pass to the test.
    provided_random = generator_kwargs.pop('random', None)
    settings = generator_kwargs.pop('settings', None) or Settings.default

    if (provided_random is not None) and settings.derandomize:
        raise InvalidArgument(
            'Cannot both be derandomized and provide an explicit random')

    if not (generator_arguments or generator_kwargs):
        raise InvalidArgument(
            'given must be called with at least one argument')

    if generator_arguments and generator_kwargs:
        note_deprecation(
            'Mixing positional and keyword arguments in a call to given is '
            'deprecated. Use one or the other.', settings
        )

    def run_test_with_generator(test):
        if settings.derandomize:
            assert provided_random is None
            random = Random(
                function_digest(test)
            )
        else:
            random = provided_random or Random()

        original_argspec = inspect.getargspec(test)
        if original_argspec.varargs:
            raise InvalidArgument(
                'varargs are not supported with @given'
            )
        extra_kwargs = [
            k for k in generator_kwargs if k not in original_argspec.args]
        if extra_kwargs and not original_argspec.keywords:
            raise InvalidArgument(
                '%s() got an unexpected keyword argument %r' % (
                    test.__name__,
                    extra_kwargs[0]
                ))
        if (
            len(generator_arguments) > len(original_argspec.args)
        ):
            raise InvalidArgument((
                'Too many positional arguments for %s() (got %d but'
                ' expected at most %d') % (
                    test.__name__, len(generator_arguments),
                    len(original_argspec.args)))
        arguments = original_argspec.args + sorted(extra_kwargs)
        specifiers = list(generator_arguments)
        seen_kwarg = None
        for a in arguments:
            if a in generator_kwargs:
                seen_kwarg = seen_kwarg or a
                specifiers.append(generator_kwargs[a])
            else:
                if seen_kwarg is not None:
                    raise InvalidArgument((
                        'Argument %s comes after keyword %s which has been '
                        'specified, but does not itself have a '
                        'specification') % (
                        a, seen_kwarg
                    ))

        argspec = inspect.ArgSpec(
            args=arguments,
            keywords=original_argspec.keywords,
            varargs=original_argspec.varargs,
            defaults=tuple(map(HypothesisProvided, specifiers))
        )

        if settings.database:
            storage = settings.database.storage(
                fully_qualified_name(test))
        else:
            storage = None

        @copy_argspec(
            test.__name__, argspec
        )
        def wrapped_test(*arguments, **kwargs):
            selfy = None
            # Because we converted all kwargs to given into real args and
            # error if we have neither args nor kwargs, this should always
            # be valid
            assert argspec.args
            selfy = kwargs.get(argspec.args[0])
            if isinstance(selfy, HypothesisProvided):
                selfy = None
            test_runner = executor(selfy)

            for example in getattr(
                wrapped_test, 'hypothesis_explicit_examples', ()
            ):
                if example.args:
                    example_kwargs = dict(zip(
                        argspec.args[-len(example.args):], example.args
                    ))
                else:
                    example_kwargs = dict(example.kwargs)

                for k, v in kwargs.items():
                    if not isinstance(v, HypothesisProvided):
                        example_kwargs[k] = v

                test_runner(
                    lambda: test(*arguments, **example_kwargs)
                )

            if not any(
                isinstance(x, HypothesisProvided)
                for xs in (arguments, kwargs.values())
                for x in xs
            ):
                # All arguments have been satisfied without needing to invoke
                # hypothesis
                test_runner(lambda: test(*arguments, **kwargs))
                return

            def convert_to_specifier(v):
                if isinstance(v, HypothesisProvided):
                    return strategy(v.value, settings)
                else:
                    return sd.just(v)

            given_specifier = sd.tuples(
                sd.tuples(*map(convert_to_specifier, arguments)),
                sd.fixed_dictionaries({
                    k: convert_to_specifier(v) for k, v in kwargs.items()})
            )

            search_strategy = strategy(given_specifier, settings)
            user_label_counts = Counter()

            def classify_template(xs):
                classify_labels = set()

                def incorporate(label):
                    classify_labels.add(UserClassification(label))
                    user_label_counts[label] += 1

                try:
                    with use_classifier(incorporate):
                        test_runner(reify_and_execute(
                            search_strategy, xs, test,
                            always_print=settings.max_shrinks <= 0
                        ))
                except UnsatisfiedAssumption as e:
                    raise e
                except Exception as e:
                    if settings.max_shrinks <= 0:
                        raise e
                    verbose_report(traceback.format_exc)
                    classify_labels.add(TestFailure(type(e)))
                return classify_labels
            classify_template.__name__ = 'classify_template(%s)' % (
                test.__name__,
            )
            tracker = Tracker()
            start_time = time.time()
            satisfying_examples = [0]
            templates_with_labels = multifind_internal(
                search_strategy, classify_template,
                settings=settings, random=random, storage=storage,
                tracker=tracker, satisfying_examples=satisfying_examples,
                start_time=start_time
            )
            falsifying_templates = [
                template
                for template, labels in templates_with_labels
                if any(isinstance(l, TestFailure) for l in labels)
            ]
            if not falsifying_templates:
                if ((
                    len(tracker) < search_strategy.template_upper_bound
                    or satisfying_examples[0] == 0
                ) and
                    satisfying_examples[0] < min(
                        settings.min_satisfying_examples,
                        settings.max_iterations,
                        settings.max_examples,
                )
                ):
                    if time_to_call_it_a_day(settings.timeout, start_time):
                        raise Timeout((
                            'Ran out of time before finding a satisfying '
                            'example for %s.'
                            ' Only found %d examples (%d satisfying '
                            'assumptions) in %.2fs.'
                        ) % (
                            get_pretty_function_description(classify_template),
                            len(tracker), satisfying_examples[
                                0], time.time() - start_time
                        ))
                    else:
                        raise Unsatisfiable((
                            'Unable to satisfy assumptions of hypothesis %s. '
                            'Only %d out of %d examples considered satisfied '
                            'assumptions'
                        ) % (
                            get_pretty_function_description(classify_template),
                            satisfying_examples[0], len(tracker)))
                else:
                    return
            else:
                falsifying_template = falsifying_templates[0]

            with settings:
                test_runner(reify_and_execute(
                    search_strategy, falsifying_template, test,
                    print_example=True
                ))

                test_runner(reify_and_execute(
                    search_strategy, falsifying_template, test_is_flaky(test),
                    print_example=True
                ))

        wrapped_test.__name__ = test.__name__
        wrapped_test.__doc__ = test.__doc__
        wrapped_test.is_hypothesis_test = True
        wrapped_test.hypothesis_explicit_examples = getattr(
            test, 'hypothesis_explicit_examples', []
        )
        wrapped_test.hypothesis_storage = storage
        return wrapped_test
    return run_test_with_generator


def find(specifier, condition, settings=None, random=None, storage=None):
    settings = settings or Settings(
        max_examples=2000,
        min_satisfying_examples=0,
        max_shrinks=2000,
    )

    search = strategy(specifier, settings)

    if storage is None and settings.database is not None:
        storage = settings.database.storage(
            'find(%s)' % (
                binascii.hexlify(function_digest(condition)).decode('ascii'),
            )
        )

    random = random or Random()
    successful_examples = [0]

    def template_condition(template):
        result = search.reify(template)
        success = condition(result)

        if success:
            successful_examples[0] += 1

        if not successful_examples[0]:
            verbose_report(lambda: 'Trying example %s' % (
                repr(result),
            ))
        elif success:
            if successful_examples[0] == 1:
                verbose_report(lambda: 'Found satisfying example %s' % (
                    repr(result),
                ))
            else:
                verbose_report(lambda: 'Shrunk example to %s' % (
                    repr(result),
                ))
        return success

    template_condition.__name__ = condition.__name__
    tracker = Tracker()

    try:
        return search.reify(best_satisfying_template(
            search, random, template_condition, settings,
            tracker=tracker, max_parameter_tries=2,
            storage=storage,
        ))
    except Timeout:
        raise
    except NoSuchExample:
        if search.template_upper_bound <= len(tracker):
            raise DefinitelyNoSuchExample(
                get_pretty_function_description(condition),
                search.template_upper_bound,
            )
        raise NoSuchExample(get_pretty_function_description(condition))


AssumptionNotMet = namedtuple('AssumptionNotMet', 'stack')
Empty = namedtuple('Empty', ())


def multifind_internal(
    strategy, classify_template, settings=None, random=None, storage=None,
    tracker=None, satisfying_examples=None, start_time=None
):
    if start_time is None:
        start_time = time.time()
    if tracker is None:
        tracker = Tracker()

    if settings is None:
        settings = Settings.default

    max_iterations = max(settings.max_iterations, settings.max_examples)
    max_examples = min(max_iterations, settings.max_examples)

    if storage is None and settings.database is not None:
        storage = settings.database.storage(
            'multifind(%s)' % (
                binascii.hexlify(
                    function_digest(classify_template)).decode('ascii'),
            )
        )

    if random is None:
        if settings.derandomize:
            random = Random(
                function_digest(classify_template)
            )
        else:
            random = Random()

    result = {}
    successful_shrinks = [0]

    def consider_template_for_label(template, label):
        if label not in result:
            result[label] = template
            return True
        if strategy.strictly_simpler(template, result[label]):
            result[label] = template
            successful_shrinks[0] += 1
            return True
        return False

    if satisfying_examples is None:
        satisfying_examples = [0]

    examples_considered = [0]

    def install_template(template):
        examples_considered[0] += 1
        if tracker.track(template) > 1:
            return False
        try:
            with settings:
                labels = set(classify_template(template))
            satisfying_examples[0] += 1
            if not labels:
                consider_template_for_label(template, Empty())
            else:
                improving = False
                for l in labels:
                    if consider_template_for_label(template, l):
                        debug_report(
                            lambda: 'Improving label %r' % (l,))
                        improving = True
                return improving
        except UnsatisfiedAssumption:
            return False

    start_time = time.time()

    def stop_now(budget):
        if len(tracker) >= strategy.template_upper_bound:
            return True
        if examples_considered[0] >= max_iterations:
            return True
        if time_to_call_it_a_day(settings.timeout * budget, start_time):
            return True
        return False

    if storage is not None:
        for template in storage.fetch(strategy):
            if stop_now(0.5):
                break
            install_template(template)
            if satisfying_examples[0] >= max_examples:
                break

    parameter_source = ParameterSource(
        random=random, strategy=strategy,
        max_tries=10,
    )

    for parameter in islice(
        parameter_source, max_iterations
    ):  # pragma: no branch
        if stop_now(0.5):
            break
        if satisfying_examples[0] >= max_examples:
            break
        template = strategy.draw_template(random, parameter)
        if not install_template(template):
            parameter_source.mark_bad()

    def yield_on_step():
        if not result:
            return
        yield
        improved = True
        while improved:
            yield
            improved = False
            pool = list(set(result.values()))
            assert pool
            strategy.arrange(pool)
            for template in pool:
                yield
                if improved:
                    break
                for simplify in strategy.simplifiers(random, template):
                    debug_report(
                        lambda: 'Applying simplifier %s' % (
                            simplify.__name__,))
                    local_change = True
                    while local_change:
                        yield
                        local_change = False
                        for simpler in simplify(random, template):
                            yield
                            if install_template(simpler):
                                local_change = True
                                improved = True
                                template = simpler
                                break
    for _ in yield_on_step():
        if stop_now(1):
            break
        if successful_shrinks[0] >= settings.max_shrinks:
            break

    if not result:
        return []

    inverted = {}
    for label, template in result.items():
        inverted.setdefault(template, set()).add(label)

    templates = list(inverted.keys())
    if storage is not None:
        for t in templates:
            storage.save(t, strategy)
    strategy.arrange(templates)
    return [(template, inverted[template]) for template in templates]


def multifind(
    strategy, classify, settings=None, random=None, storage=None
):
    """A classify function takes a value and returns an iterable over some tags
    for that value.

    multifind then returns a list of simple values drawn from strategy
    for hitting as many of those tags as it can find.

    """
    settings = settings or Settings(
        max_examples=2000,
        max_iterations=5000,
        min_satisfying_examples=0,
        max_shrinks=2000,
    )

    def classify_template(template):
        return classify(strategy.reify(template))

    templates_with_labels = multifind_internal(
        strategy, classify_template, settings, random, storage
    )
    return [
        strategy.reify(template)
        for template, labels in templates_with_labels
        if not any(isinstance(l, AssumptionNotMet) for l in labels)
    ]

load_entry_points()
