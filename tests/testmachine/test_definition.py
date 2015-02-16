from hypothesis.testmachine.testmachine import (
    MachineDefinition, ValidationError
)
import pytest


def test_can_define_non_hashable_varstack_names():
    md = MachineDefinition()
    assert md.install_varstack([int]) is not None


def test_caches_varstacks():
    md = MachineDefinition()
    assert md.install_varstack({1, 2, 3}) is md.install_varstack({1, 2, 3})


def test_installs_dependent_varstacks():
    md = MachineDefinition()
    md.install_varstack((bool, [int]))
    names = list(md.varstack_names())
    assert len(names) == 4
    assert (bool, [int]) in names
    assert bool in names
    assert int in names
    assert [int] in names


def test_is_valid_for_known_types_automatically():
    md = MachineDefinition()
    md.install_varstack([int])
    md.validate()


def test_is_not_valid_for_unknown_types_automatically():
    class Unknown(object):
        pass
    md = MachineDefinition()
    md.install_varstack(Unknown)
    with pytest.raises(ValidationError):
        md.validate()
