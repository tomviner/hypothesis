import pytest

from hypothesis.searchstrategy.data import DataDefinition, InvalidDefinition, \
    optional, rule


def test_empty_data_is_invalid():
    with pytest.raises(InvalidDefinition):
        DataDefinition().validate()


def test_rules_must_be_capitalized():
    data = DataDefinition()
    with pytest.raises(InvalidDefinition):
        data.rule('kittens')


def test_rules_must_be_valid_python_identifiers():
    data = DataDefinition()
    with pytest.raises(InvalidDefinition):
        data.rule('Kit tens')


def test_rules_must_be_strings():
    with pytest.raises(InvalidDefinition):
        rule(1)


def test_self_only_recursive_data_is_invalid():
    data = DataDefinition()
    data.define_data(
        'Selfy', selfy=rule('Selfy')
        )
    with pytest.raises(InvalidDefinition):
        data.validate()


def test_dangling_rule_is_invalid():
    data = DataDefinition()
    data.define_data(
        'A', b=rule('B'),
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
        'Nat', s=optional(rule('Nat'))
    )
    data.validate()


def test_labelled_binary_tree_is_valid():
    data = DataDefinition()
    data.define_data('Leaf', label=int)
    data.define_data('Split', left=rule('Tree'), right=rule('Tree'))
    data.define_union('Tree', 'Leaf', 'Split')
    data.validate()


def test_not_strategy_or_rule_is_invalid():
    data = DataDefinition()
    data.define_data(
        'Thing', x="kittens"
    )
    with pytest.raises(InvalidDefinition):
        data.validate()


def test_can_instantiate_data_definition_types():
    data = DataDefinition()
    data.define_data('Leaf', label=int)
    data.define_data('Split', left=rule('Tree'), right=rule('Tree'))
    data.define_union('Tree', 'Leaf', 'Split')
    data.validate()

    assert isinstance(data.Leaf(2), data.Leaf)
    assert isinstance(data.Leaf("foo"), data.Leaf)
    assert isinstance(data.Split(left="foo", right=data.Leaf(1)), data.Split)


def test_union_types_are_superclasses():
    data = DataDefinition()
    data.define_data('Leaf')
    data.define_data('Split')
    data.define_union('Tree', 'Leaf', 'Split')
    data.validate()
    assert issubclass(data.Leaf, data.Tree)
    assert issubclass(data.Split, data.Tree)
    assert not issubclass(data.Split, data.Leaf)
    assert not issubclass(data.Leaf, data.Split)
