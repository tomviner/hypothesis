from random import Random
from .context import requirements, consume


class Operation(object):
    def __init__(
            self, argspec, target=None, targets=None, name=None, pattern=None,
            patterns=None):
        if pattern and patterns:
            raise ValueError(
                "Cannot specify both a single and multiple patterns"
            )
        if pattern:
            patterns = (pattern,)
        if target and targets:
            raise ValueError(
                "Cannot specify both a single and multiple targets"
            )
        if target is not None:
            self.single_target = True
            targets = (target,)
        else:
            self.single_target = False
        if targets is None:
            targets = ()
        if len(targets) == 1:
            self.target = targets[0]
        self.argspec = argspec
        self.targets = targets
        self.name = name or self.__class__.__name__.lower()
        self.requirements = requirements(argspec)
        self.patterns = patterns

    def applicable(self, heights):
        for varstack, req in self.requirements.items():
            if heights.get(varstack, 0) < req:
                return False
        return True

    def __repr__(self):
        return "Operation(%s)" % self.display()

    def compile(self, arguments, results):
        if self.patterns is None:
            invocation = "{0}({1})".format(self.name, ', '.join(arguments))
            if results:
                invocation = "%s = %s" % (', '.join(results), invocation)
            return [invocation]
        else:
            patterns = self.patterns
            if results:
                patterns = list(patterns)
                patterns[-1] = "%s = %s" % (', '.join(results), patterns[-1])
            return [
                pattern.format(*arguments)
                for pattern in patterns
            ]

    def args(self):
        return ()

    def display(self):
        return "%s(%s)" % (
            self.name, ', '.join(map(repr, self.args()))
        )

    def invoke(self, context):
        raise NotImplementedError("%s.invoke(context)" % (self.__class__,))

    def simulate(self, context):
        context.read(self.argspec)
        for t in self.targets:
            context.varstack(t).push(None)


class ReadAndWrite(Operation):
    def __init__(
        self, function, **kwargs
    ):
        if 'name' not in kwargs:
            kwargs['name'] = function.__name__

        super(ReadAndWrite, self).__init__(**kwargs)
        self.function = function

    def invoke(self, context):
        args = context.read(self.argspec)
        result = self.function(*args)
        if self.targets:
            if self.single_target:
                context.varstack(self.targets[0]).push(result)
            else:
                assert len(self.targets) == len(result)
                for target, v in zip(self.targets, result):
                    context.varstack(target).push(v)


class Mutate(ReadAndWrite):
    def __init__(
        self, function, argspec, name=None,
        pattern=None
    ):
        super(Mutate, self).__init__(
            argspec=argspec,
            name=name or function.__name__,
            pattern=pattern,
        )


class BinaryOperator(ReadAndWrite):
    def __init__(self, operation, varstack, name):
        super(BinaryOperator, self).__init__(
            function=operation,
            argspec=(varstack, varstack),
            target=varstack,
            name=name,
        )

    def compile(self, arguments, results):
        assert len(arguments) == 2
        assert len(results) <= 1
        x, y = arguments
        invocation = " ".join((x, self.name, y))
        if results:
            return ["%s = %s" % (', '.join(results), invocation)]
        else:
            return [invocation]


class UnaryOperator(ReadAndWrite):
    def __init__(self, operation, varstack, name):
        super(UnaryOperator, self).__init__(
            function=operation,
            argspec=(varstack,),
            target=varstack,
            name=name
        )

    def compile(self, arguments, results):
        assert len(arguments) == 1
        assert len(results) <= 1
        invocation = "".join((self.name, arguments[0]))
        if results:
            return ["{0} = {1}".format(', '.join(results), invocation)]
        else:
            return [invocation]


class Check(Operation):
    def __init__(self, test, argspec, name=None, pattern=None, patterns=None):
        name = name or test.__name__
        if pattern is None and patterns is None:
            arg_string = ', '.join(
                ["{%d}" % (x,) for x in range(len(argspec))]
            )
            pattern = "assert %s(%s)" % (name, arg_string)

        super(Check, self).__init__(
            argspec=argspec, name=name, pattern=pattern, patterns=patterns
        )
        self.argspec = argspec
        self.test = test

    def invoke(self, context):
        args = context.read(self.argspec)
        assert self.test(*args)


class Push(Operation):
    def __init__(self, varstack, gen_value, value_formatter=None):
        super(Push, self).__init__(argspec=(), target=varstack, name="push")
        self.gen_value = gen_value
        self.value_formatter = value_formatter or repr

    def compile(self, arguments, results):
        assert not arguments
        assert len(results) <= 1
        v = self.gen_value()
        return [
            "%s = %s" % (results[0], self.value_formatter(v))
        ]

    def args(self):
        return (self.gen_value(),)

    def invoke(self, context):
        context.varstack(self.target).push(self.gen_value())


class InapplicableLanguage(Exception):
    pass


class Language(object):
    def generate(self, heights, random):
        """
        :param heights: A dict of string names to integer counts of the number
            of values available each varstack
        :param a random number generator

        returns an Operation or raises InapplicableLanguage. Should not depend
        on any factors other than its parameters. Whether it raises an
        InapplicableLanguage should not depend on the state of the random
        number generator.
        """
        raise NotImplementedError()

    def generate_from(self, context):
        return self.generate(context.heights(), context.random)


class PushRandom(Language):
    def __init__(self, produce, target, name=None, value_formatter=None):
        super(PushRandom, self).__init__()
        self.produce = produce
        self.target = target
        self.value_formatter = value_formatter

    def generate(self, heights, random):
        state = random.getstate()

        def gen_result():
            r = Random(0)
            r.setstate(state)
            return self.produce(r)

        # We run this so that any errors bubble up rather than being treated
        # as a breaking program.
        gen_result()

        return Push(
            self.target,
            gen_result,
            value_formatter=self.value_formatter,
        )


class ChooseFrom(Language):
    def __init__(self, children):
        super(ChooseFrom, self).__init__()
        adjusted = []
        for c in children:
            if isinstance(c, (tuple, list)):
                c = ChooseFrom(c)
            adjusted.append(c)
        children = tuple(adjusted)
        self.children = children

    def generate(self, heights, random):
        children = list(self.children)
        random.shuffle(children)
        for child in children:
            try:
                if isinstance(child, Operation):
                    operation = child
                else:
                    operation = child.generate(heights, random)
                if operation.applicable(heights):
                    return operation
            except InapplicableLanguage:
                continue
        raise InapplicableLanguage


class Drop(Operation):
    def __init__(self, varstack):
        super(Drop, self).__init__(
            argspec=(consume(varstack),)
        )

    def invoke(self, context):
        context.read(self.argspec)

    def compile(self, arguments, results):
        return []


class DataShufflingOperation(Operation):
    def __init__(self, varstack):
        super(DataShufflingOperation, self).__init__(
            argspec=(varstack,) * self.height
        )
        self.varstack = varstack

    def simulate(self, context):
        return self.invoke(context)

    def compile(self, arguments, results):
        return []


class Dup(DataShufflingOperation):
    height = 1

    def invoke(self, context):
        context.varstack(self.varstack).dup()


class Swap(DataShufflingOperation):
    height = 2

    def invoke(self, context):
        context.varstack(self.varstack).swap()


class Rot(DataShufflingOperation):
    height = 3

    def invoke(self, context):
        context.varstack(self.varstack).rot()
