from __future__ import division, print_function, absolute_import, \
    unicode_literals

from hypothesis.errors import InvalidArgument
from hypothesis.internal.compat import text_type, binary_type
from hypothesis.utils.dynamicvariables import DynamicVariable


classification_receiver = DynamicVariable(None)


def classify(label):
    if not isinstance(label, (text_type, binary_type)):
        raise InvalidArgument('Expected string label but got %r of type %s' % (
            label, type(label).__name__
        ))
    current_receiver = classification_receiver.value
    if current_receiver is None:
        return
    else:
        current_receiver(label)


def use_classifier(new_classifier):
    return classification_receiver.with_value(new_classifier)
