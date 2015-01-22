from contextlib import contextmanager
import sys
import os
import re

TRAILING_PY = re.compile(r"\.py$")


@contextmanager
def directory_on_path(d):
    if sys.path[0] == d:
        yield
    else:
        try:
            sys.path.insert(0, d)
            yield
        finally:
            sys.path.remove(d)


class BadImport(Exception):
    pass


def import_file(f):
    location = os.path.dirname(f)
    module_name = TRAILING_PY.sub("", os.path.basename(f))
    with directory_on_path(location):
        return __import__(module_name)


def import_files(path):
    if not os.path.exists(path):
        raise BadImport("No such file %r" % (path,))
    elif os.path.isdir(path):
        with directory_on_path(path):
            for f in os.listdir(path):
                if TRAILING_PY.search(f):
                    yield import_file(os.path.join(path, f))
    elif not TRAILING_PY.match(path):
        raise ValueError("Not a python file %r" % (path,))
    else:
        yield import_file(path)
