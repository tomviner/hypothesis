from hypothesis.searchstrategy.data import DataDefinition
from hypothesis.internal.debug import minimal

BinaryTrees = DataDefinition()
Tree = BinaryTrees.define_union('Tree', 'Leaf', 'Split')
BinaryTrees.define_data('Leaf', label=int)
BinaryTrees.define_data('Split', left=Tree, right=Tree)
BinaryTrees.validate()


def depth(x):
    if isinstance(x, BinaryTrees.Leaf):
        return 1
    else:
        return max(depth(x.left), depth(x.right)) + 1


def test_minimizes_leaf():
    assert minimal(BinaryTrees.Leaf) == BinaryTrees.Leaf(label=0)


def test_minimizes_split():
    assert minimal(BinaryTrees.Split) == BinaryTrees.Split(
        BinaryTrees.Leaf(0),
        BinaryTrees.Leaf(0),
    )


def test_minimizes_tree():
    assert minimal(BinaryTrees.Tree) == BinaryTrees.Leaf(0)
