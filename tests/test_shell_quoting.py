#!/usr/bin/env wizzer

from dataclasses import dataclass
import os
import sys

from jiig.util.process import simple_shell_quote


@dataclass
class Test:
    value: str
    argument: str
    literal: str


@dataclass
class Error:
    label: str
    expected: str
    received: str


TESTS = [
    Test('abc', 'abc', 'abc'),
    Test('ab c', '"ab c"', "'ab c'"),
    Test('"abc"', r'"\"abc\""', """'"abc"'"""),
    Test('"abc" ', r'"\"abc\" "', """'"abc" '"""),
    Test(r'xy\z', r'"xy\z"', r"'xy\z'"),
]

ERRORS = []


# noinspection DuplicatedCode
def run_tests():
    for test in TESTS:
        argument = simple_shell_quote(test.value)
        literal = simple_shell_quote(test.value, literal=True)
        if argument != test.argument:
            ERRORS.append(Error('argument', test.argument, argument))
        if literal != test.literal:
            ERRORS.append(Error('literal', test.literal, literal))
    for error in ERRORS:
        sys.stderr.write(f'ERROR[{error.label}]:'
                         f' expected: {error.expected},'
                         f' received: {error.received}{os.linesep}')
    if ERRORS:
        sys.stderr.write(f'* {len(ERRORS)} of {len(TESTS) * 2} tests failed *')
    else:
        sys.stdout.write(f'All tests passed.')
    sys.stdout.write(os.linesep)
    sys.exit(len(ERRORS))


if __name__ == '__main__':
    run_tests()
