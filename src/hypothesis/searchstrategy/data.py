from hypothesis.errors import HypothesisException
from hypothesis.settings import Settings
from hypothesis.searchstrategy import strategy, SearchStrategy
from hypothesis.internal.reflection import is_valid_identifier
from hypothesis.internal.compat import string_types

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


class Types(object):
    pass


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


def rule(name):
    check_rule_name(name)
    return RuleProxy(name)


class DataDefinition(object):
    def __init__(self, settings=None):
        self.settings = settings or Settings.default
        self.validated = False
        self.rules = {}

    def install_type(self, name, members):
        check_rule_name(name)
        members = tuple(sorted(members))
        existing = getattr(self, name, None)
        if existing is not None and existing._fields == members:
            return
        setattr(self, name, namedtuple(name, members))

    def define_data(self, name, **members):
        result = RuleDefinition(name, members)
        self.install_type(name, members)
        self.validated = False
        self.rules[name] = result
        return result

    def define_union(self, name, *alternatives):
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

        self.validated = True
