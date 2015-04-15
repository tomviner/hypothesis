import pytest

from hypothesis.searchstrategy.data import DataDefinition, InvalidDefinition, \
    optional


def test_empty_data_is_invalid():
    with pytest.raises(InvalidDefinition):
        DataDefinition().validate()


def test_self_only_recursive_data_is_invalid():
    data = DataDefinition()
    data.define_rule(
        'Selfy', selfy=data.rule('Selfy')
        )
    with pytest.raises(InvalidDefinition):
        data.validate()


def test_dangling_rule_is_invalid():
    data = DataDefinition()
    data.define_rule(
        'A', b=data.rule('B'),
    )
    with pytest.raises(InvalidDefinition):
        data.validate()


def test_pure_struct_data_is_valid():
    data = DataDefinition()
    data.define_rule(
        'Thing', x=int, y=int
    )
    data.validate()


def test_optional_self_recursion_is_valid():
    data = DataDefinition()
    data.define_rule(
        'Nat', s=optional(data.rule('Nat'))
    )
    data.validate()


def test_labelled_binary_tree_is_valid():
    data = DataDefinition()
    data.define_rule('Leaf', label=int)
    data.define_rule('Split', left=data.rule('Tree'), right=data.rule('Tree'))
    data.define_union('Tree', 'Leaf', 'Split')
    data.validate()


def test_not_strategy_or_rule_is_invalid():
    data = DataDefinition()
    data.define_rule(
        'Thing', x="kittens"
    )
    with pytest.raises(InvalidDefinition):
        data.validate()
