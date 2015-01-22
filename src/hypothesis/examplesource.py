from random import Random
from hypothesis.internal.compat import hrange


class ExampleSource(object):

    """An object that provides you with an a stream of examples to work with.

    Starts by fetching examples from storage if storage has been provided but
    if storage is None will happily continue without. Follows by generating new
    examples, but if the strategy is None then will stop there. Must have at
    least one of strategy and storage but does not have to have both.

    This does not handle deduplication or make decisions as to when to stop.
    That's up to the caller.

    """

    def __init__(
        self, random, strategy,
        storage, min_parameters=50
    ):
        if not isinstance(random, Random):
            raise ValueError('A Random is required but got %r' % (random,))
        if strategy is None and storage is None:
            raise ValueError(
                'Cannot proceed without at least one way of getting examples'
            )
        self.strategy = strategy
        self.storage = storage
        self.random = random
        self.parameters = []
        self.last_parameter_index = -1
        self.min_parameters = min_parameters
        self.bad_counts = []
        self.good_counts = []
        self.total_good_counts = 0
        self.total_bad_counts = 0
        self.total_counts = 0
        self.counts = []
        self.is_new_parameter = True
        self.new_parameter_bad = 0
        self.new_parameter_good = 0
        self.mark_set = False
        self.started = False

    def quality_counts(self, param):
        if param < 0:
            seen = len(self.parameters)
            good = self.new_parameter_good
            bad = self.new_parameter_bad
        else:
            seen = self.counts[param]
            good = self.good_counts[param]
            bad = self.bad_counts[param]
        neutral = seen - good - bad
        return (bad, neutral, good)

    def prior(self):
        neutral_counts = (
            self.total_counts - self.total_bad_counts - self.total_good_counts
        )
        assert neutral_counts >= 0
        prior = [
            1.0 + self.total_bad_counts,
            1.0 + neutral_counts,
            1.0 + self.total_good_counts
        ]
        total = sum(prior)
        for i in hrange(3):
            prior[i] *= (2 / total)
        return prior

    def score_parameter(self, param):
        """
        Concept: We are basically doing Thompson sampling on a multi-armed
        bandit, but each arm can have three outcomes: Bad, neutral or good.

        We have a Dirichlet prior for each of the three likelihoods. The score
        is a draw from the prior followed by an expected value of the resulting
        distribution, where the value of a good example is +1 and the value of
        a bad example is -1.

        The prior is itself derived empirically from the data we've seen so far
        in a manner I'm going to nod sagely and claim is definitely a form of
        empirical Bayes. It is set to a total weight of 2 (meaning "we believe
        we've got about 2 examples worth of evidence for this") with the
        expected probability of each outcome being a slightly smoothed away
        from zero version of the probability of having seen each outcome in all
        calls so far. This lets us adapt well to any particular distribution of
        good or bad values and not treat the unknown as more exciting than it
        is likely to prove.
        """
        bad, neutral, good = self.quality_counts(param)
        prior = self.prior()
        bp = bad + prior[0]
        np = neutral + prior[1]
        gp = good + prior[2]
        assert bp > 0
        assert np > 0
        assert gp > 0
        a = self.random.betavariate(bp, np + gp)
        b = self.random.betavariate(np, gp) * (1 - a)
        c = 1.0 - a - b
        return c - a

    def mark(self, good):
        if not self.started:
            raise ValueError('No examples have been generated yet')
        if self.mark_set:
            raise ValueError('This parameter has already been marked')
        self.mark_set = True
        if self.last_parameter_index < 0:
            return
        if good:
            self.good_counts[self.last_parameter_index] += 1
            self.total_good_counts += 1
            if self.is_new_parameter:
                self.new_parameter_good += 1
        else:
            self.bad_counts[self.last_parameter_index] += 1
            self.total_bad_counts += 1
            if self.is_new_parameter:
                self.new_parameter_bad += 1

    def mark_bad(self):
        """The last example was bad.

        If possible can we have less of that please?

        """
        self.mark(False)

    def mark_good(self):
        """The last example was interesting.

        More like that please?

        """
        self.mark(True)

    def new_parameter(self):
        result = self.strategy.parameter.draw(self.random)
        self.parameters.append(result)
        self.bad_counts.append(0)
        self.good_counts.append(0)
        self.counts.append(1)
        self.is_new_parameter = True
        return result

    def pick_a_parameter(self):
        self.mark_set = False
        self.total_counts += 1
        if len(self.parameters) < self.min_parameters:
            return self.new_parameter()
        else:
            best_score = self.score_parameter(-1)
            best_index = -1

            for i in hrange(len(self.parameters)):
                assert self.counts[i] > 0
                assert self.bad_counts[i] >= 0
                assert self.bad_counts[i] <= self.counts[i]

                score = self.score_parameter(i)
                if score > best_score:
                    best_score = score
                    best_index = i
            if best_index < 0:
                self.last_parameter_index = len(self.parameters)
                return self.new_parameter()
            self.is_new_parameter = False
            self.last_parameter_index = best_index
            self.counts[self.last_parameter_index] += 1
            return self.parameters[self.last_parameter_index]

    def __iter__(self):
        self.started = True
        if self.storage is not None:
            for example in self.storage.fetch():
                self.mark_set = False
                yield example

        if self.strategy is not None:
            while True:
                parameter = self.pick_a_parameter()
                yield self.strategy.produce(
                    self.random, parameter
                )
