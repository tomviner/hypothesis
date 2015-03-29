import os
import sys
import subprocess

from hypothesis import given


@given(str)
def test_exact_details_irrelevant(s):
    """
    Just here to ensure that there's a @given call
    """
    pass


def test_sys_path():
    assert all(isinstance(s, str) for s in sys.path)


def test_pathsep():
    assert isinstance(os.pathsep, str)


def test_subprocess():
    """
    Check that Hypothesis's path changes haven't broken the ability to us
    it in the env of a subprocess
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    subprocess.check_call(["python", "--version"], env=env)
