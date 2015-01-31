import sys
from hypothesis.internal.discovery import import_files, tests_in_module


def main(files):
    modules = import_files(files)
    for module in modules:
        tests = list(tests_in_module(module))
        if tests:
            print(module.__name__)
            for k, v in tests:
                print(k)
                v()

if __name__ == '__main__':
    main(sys.argv[1:])
