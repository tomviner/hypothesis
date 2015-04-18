from hypothesis.errors import HypothesisException
from hypothesis.settings import Settings
from hypothesis.searchstrategy import strategy, SearchStrategy
from hypothesis.internal.reflection import is_valid_identifier
from hypothesis.internal.compat import string_types
import inspect

from collections import namedtuple


class InvalidDefinition(HypothesisException):
    pass


class Rule(object):
    def __init__(self, name):
        self.name = name


class RuleDefinition(Rule):
    def __init__(self, name, members):
        super(RuleDefinition, self).__init__(name)
        self.members = dict(members)

    def sources(self):
        return [
            v.name
            for v in self.members.values()
            if isinstance(v, Rule)
        ]


class UnionDefinition(Rule):
    def __init__(self, name, alternatives):
        super(UnionDefinition, self).__init__(name)
        self.alternatives = tuple(alternatives)

    def sources(self):
        return [
            v.name
            for v in self.alternatives
        ]


class optional(object):
    def __init__(self, definition):
        self.definition = definition


class RuleProxy(object):
    def __init__(self, name):
        self.name = name


def check_rule_name(name):
    if not isinstance(name, string_types):
        raise InvalidDefinition(
            "%r is not a string" % (name,)
        )
    if not is_valid_identifier(name):
        raise InvalidDefinition(
            "%r is not a valid python identifier" % (name,)
        )
    if name[0] != name[0].upper():
        raise InvalidDefinition(
            "Invalid rule name %s: Rules must be capitalized" % (
                name,
            )
        )


class RuleType(object):
    pass


class DataDefinitionType(RuleType):
    pass


def rule(name):
    check_rule_name(name)
    return RuleProxy(name)


class DataDefinition(object):
    def __init__(self, settings=None):
        self.settings = settings or Settings.default
        self.validated = False
        self.rules = {}

    def _define_union_type(self, name, parents, stack=None):
        check_rule_name(name)
        if stack is None:
            stack = []
        existing = getattr(self, name, None)
        if existing is not None:
            assert issubclass(existing, RuleType)
            return existing
        if name in stack:
            stack.append(name)
            raise InvalidDefinition(
                "Cyclic definition of unions %s" % (" < ".join(stack),)
            )
        stack.append(name)
        l = len(stack)
        parent_types = []
        for p in parents.get(name, ()):
            parent_types.append(self._define_union_type(
                p, parents, stack
            ))
        assert len(stack) == l
        assert stack[-1] == name
        stack.pop()
        if not parent_types:
            parent_types = (RuleType,)
        T = type(name, tuple(parent_types), {})
        setattr(self, name, T)
        return T

    def define_types(self):
        for k, v in list(inspect.getmembers(self)):
            if isinstance(v, type) and issubclass(v, RuleType):
                delattr(self, k)

        parents = {}
        unions = []

        for k, v in self.rules.items():
            if isinstance(v, UnionDefinition):
                for r in v.alternatives:
                    parents.setdefault(r.name, set()).add(v.name)
                unions.append(v.name)

        for u in unions:
            self._define_union_type(u, parents)
            assert hasattr(self, u)

        for k, v in self.rules.items():
            if isinstance(v, RuleDefinition):
                self._install_type(v.name, v.members, parents.get(v.name, ()))

    def _install_type(self, name, members, parents):
        check_rule_name(name)
        members = tuple(sorted(members))

        class DDType(object):
            @classmethod
            def rule(cls):
                result = self.rule(name)
                assert isinstance(result, Rule)
                return result

            @classmethod
            def argspec(cls):
                targets = cls.rule().members
                result = []
                for m in cls._fields:
                    r = targets[m]
                    if isinstance(r, Rule):
                        result.append(r.name)
                return tuple(result)

        parents = tuple(sorted(
            (getattr(self, n) for n in parents),
            key=lambda x: x.__name__,
        )) + (
            DataDefinitionType, namedtuple(name, members), DDType)
        setattr(self, name, type(name, parents, {}))

    def define_data(self, name, **members):
        result = RuleDefinition(name, members)
        self.validated = False
        self.rules[name] = result
        return result

    def define_union(self, name, *alternatives):
        if not alternatives:
            raise InvalidDefinition("Unions must have at least one element")
        result = UnionDefinition(name, map(self.rule, alternatives))
        self.validated = False
        self.rules[name] = result
        return result

    def rule(self, name):
        check_rule_name(name)
        try:
            return self.rules[name]
        except KeyError:
            return RuleProxy(name)

    def convert(self, value):
        if isinstance(value, (SearchStrategy, Rule)):
            return value
        if isinstance(value, RuleProxy):
            if value.name in self.rules:
                return self.rules[value.name]
            raise InvalidDefinition(
                "Undefined reference to rule %s" % (
                    value.name,
                )
            )
        elif isinstance(value, optional):
            return optional(self.convert(value.definition))
        else:
            try:
                return strategy(value, self.settings)
            except NotImplementedError:
                raise InvalidDefinition(
                    "No strategy for specifier %r" % (value,)
                )

    def validate(self):
        if self.validated:
            return
        if not self.rules:
            raise InvalidDefinition("Empty DataDefinition")
        for rule in self.rules.values():
            assert isinstance(rule, (RuleDefinition, UnionDefinition))
            if isinstance(rule, RuleDefinition):
                for k, v in rule.members.items():
                    rule.members[k] = self.convert(v)
            else:
                rule.alternatives = tuple(map(self.convert, rule.alternatives))

        productive_rules = set()
        while True:
            new_productive_rules = set()
            for r in self.rules.values():
                productive_targets = (
                    s in productive_rules for s in r.sources())
                if ((
                    isinstance(r, UnionDefinition) and
                    any(productive_targets)) or (
                    isinstance(r, RuleDefinition) and
                    all(productive_targets)
                )):
                    new_productive_rules.add(r.name)
            if new_productive_rules == productive_rules:
                break
            productive_rules = new_productive_rules
        assert len(productive_rules) <= len(self.rules)
        if len(productive_rules) < len(self.rules):
            unproductive_rules = set(self.rules) - productive_rules
            raise InvalidDefinition(
                "Cannot produce instance%(s)s of rule%(s)s %(r)s" % {
                    "s": "s" if len(unproductive_rules) > 1 else "",
                    "r": ', '.join(unproductive_rules)
                }
            )
        self.define_types()
        self.validated = True


@strategy.extend_static(DataDefinitionType)
def data_type_strategy(specifier, settings):
    argspec = specifier.argspec()
    if argspec:
        raise NotImplementedError(
            "Cannot yet define strategies for non-empty argspec %r" % (
                argspec,
            )
        )
    rule = specifier.rule()
    if isinstance(rule, UnionDefinition):
        raise NotImplementedError(
            "Cannot yet define strategies for union types"
        )
    return strategy(
        specifier(*[
            rule.members[f] for f in specifier._fields
        ]),
        settings
    )


class BuildOperation(object):
    def __init__(self, rule, data):
        self.rule = rule
        self.data = data


class OperationStrategy(SearchStrategy):
    def __init__(self, data_definition, settings):
        self.data_definition = data_definition

    def produce_parameter(self, random):
        pass

    def produce_template(self, context, parameter_value):
        pass


def run_program(program):
    bundle = Bundle()
    for p in program:
        p.execute(bundle)
    return bundle


@strategy.extend(DataDefinition)
def data_definition_strategy(specifier, settings):
    return strategy([OperationStrategy(specifier, settings)], settings).map(
        run_program
    )


class Bundle(object):
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        return self.data.setdefault(key, [])
