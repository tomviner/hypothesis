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


def test_can_be_in_multiple_unions():
    data = DataDefinition()
    data.define_union('AB', 'A', 'B')
    data.define_union('BC', 'B', 'C')
    data.define_data('A')
    data.define_data('B')
    data.define_data('C')
    data.validate()
    assert issubclass(data.A, data.AB)
    assert issubclass(data.A, data.AB)
    assert not issubclass(data.C, data.AB)
    assert not issubclass(data.A, data.BC)
    assert issubclass(data.B, data.BC)
    assert issubclass(data.C, data.BC)


def test_unions_may_be_of_unions():
    data = DataDefinition()
    data.define_union('A', 'B')
    data.define_union('B', 'C')
    data.define_data('C')
    data.validate()

    assert issubclass(data.C, data.B)
    assert issubclass(data.C, data.A)
    assert issubclass(data.B, data.A)


def test_unions_may_be_of_multiple_unions():
    data = DataDefinition()
    data.define_union('A', 'C')
    data.define_union('B', 'C')
    data.define_union('C', 'D')
    data.define_data('D')
    data.validate()

    assert issubclass(data.C, data.B)
    assert issubclass(data.C, data.A)
    assert not issubclass(data.B, data.A)
    assert issubclass(data.D, data.C)


def test_unions_may_not_be_empty():
    data = DataDefinition()
    with pytest.raises(InvalidDefinition):
        data.define_union('A')


def test_unions_may_not_be_recursive():
    data = DataDefinition()
    data.define_union('A', 'B', 'C')
    data.define_union('B', 'A', 'C')
    data.define_data('C')
    with pytest.raises(InvalidDefinition):
        data.validate()


def test_unions_may_not_be_indirectly_recursive():
    data = DataDefinition()
    data.define_union('A', 'B', 'D')
    data.define_union('B', 'C', 'D')
    data.define_union('C', 'A', 'D')
    data.define_data('D')
    with pytest.raises(InvalidDefinition):
        data.validate()
