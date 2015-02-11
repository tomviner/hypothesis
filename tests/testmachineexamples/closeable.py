"""
Demonstrating the "consume" feature, which allows you to mark operations as
making values invalid afterwards. If it didn't work this would generate a small
test case which tried to use toggle() after lock(), but instead it fails to
find a test case.

Example output:
    Unable to find a failing program of length <= 200 after 500 iterations
"""

from hypothesis.testmachine import TestMachine, consume
from hypothesis.testmachine.common import operation, generate, basic_operations
from hypothesis.testmachine.operations import Dup

machine = TestMachine()


class Button(object):
    def __init__(self):
        self.locked = False

    def lock(self):
        self.locked = True

    def toggle(self):
        if self.locked:
            raise ValueError("Cannot toggle a locked button")

machine.add(
    generate(
        lambda _: Button(), "buttons", value_formatter=lambda b: "Button()"
    ),
    operation(
        function=lambda x: x.lock(),
        argspec=(consume("buttons"),),
        target=None,
        name="lock",
        pattern="{0}.lock()"
    ),
    operation(
        function=lambda x: x.toggle(),
        argspec=("buttons",),
        target=None,
        name="toggle",
        pattern="{0}.toggle()"
    ),
    Dup("buttons"),
    basic_operations("buttons"),
)

if __name__ == '__main__':
    machine.main()
