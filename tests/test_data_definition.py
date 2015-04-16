import pytest

from hypothesis.searchstrategy.data import DataDefinition, InvalidDefinition, \
    optional


def test_empty_data_is_invalid():
    with pytest.raises(InvalidDefinition):
        DataDefinition().validate()


def test_self_only_recursive_data_is_invalid():
    data = DataDefinition()
    data.define_data(
        'Selfy', selfy=data.rule('Selfy')
        )
    with pytest.raises(InvalidDefinition):
        data.validate()


def test_dangling_rule_is_invalid():
    data = DataDefinition()
    data.define_data(
        'A', b=data.rule('B'),
    )
    with pytest.raises(InvalidDefinition):
        data.validate()


def test_pure_struct_data_is_valid():
    data = DataDefinition()
    data.define_data(
        'Thing', x=int, y=int
    )
    data.validate()


def test_optional_self_recursion_is_valid():
    data = DataDefinition()
    data.define_data(
        'Nat', s=optional(data.rule('Nat'))
    )
    data.validate()


def test_labelled_binary_tree_is_valid():
    data = DataDefinition()
    data.define_data('Leaf', label=int)
    data.define_data('Split', left=data.rule('Tree'), right=data.rule('Tree'))
    data.define_union('Tree', 'Leaf', 'Split')
    data.validate()


def test_not_strategy_or_rule_is_invalid():
    data = DataDefinition()
    data.define_data(
        'Thing', x="kittens"
    )
    with pytest.raises(InvalidDefinition):
        data.validate()
