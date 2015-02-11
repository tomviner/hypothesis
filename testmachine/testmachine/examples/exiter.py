"""
Demonstration that testmachine supports programs where the error causes the
whole program to exit. Must be run with --fork

Example output:
    die()
"""

from testmachine import TestMachine
from testmachine.common import operation
import os
import traceback

machine = TestMachine()


def die():
    traceback.print_stack()
    os._exit(1)


machine.add(
    operation(die, argspec=())
)

if __name__ == '__main__':
    machine.fork = True
    machine.main()
