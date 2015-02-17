from hypothesis.testmachine.testmachine import MachineDefinition
from itertools import islice
import random


def test_can_generate_and_run_a_program():
    s = (bool, [int])
    md = MachineDefinition()
    md.install_varstack(s)
    program = list(islice(md.build_program(random), 200))
    final_context = md.run_program(program)
    assert final_context.height(s) > 0
