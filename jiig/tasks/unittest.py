# Copyright (C) 2021-2023, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""Jiig task that can run unit tests.

Uses Python standard library unittest to run named or all unit tests, but
enhances it by being able to find test methods without needing the TestCase
class name.

TODO: Support tool tests, e.g. with TOOL specifier option.
"""

import sys
from importlib import import_module
from inspect import (
    getsourcelines,
    isclass,
)
from unittest import (
    TestLoader,
    TextTestRunner,
)
from unittest.case import TestCase
from unittest.suite import TestSuite

import jiig
from jiig.util.filesystem import check_folder_exists
from jiig.util.log import log_error


@jiig.task
def unittest_(
    runtime: jiig.Runtime,
    tests: jiig.f.text(repeat=()),
    name_sort: jiig.f.boolean(),
):
    """Run unit tests using Python standard library unittest module.

    Test names can be:
    * <module-name>
    * <module-name>.<TestCase>
    * <module-name>.<TestCase>.<test>
    * <module-name>.<test>

    See the Python documentation for `unittest.loadTestsFromNames()` for more
    information.

    Adds support for <module-name>.<test> by scanning module test case classes.

    Responds to Jiig verbose option by making unittest output more verbose.

    Uses custom TestLoader to run tests sorted by relative source position,
    rather than method name. Can optionally use name sort if name_sort=True.

    Args:
        runtime: jiig Runtime API
        tests: test names to run, or all tests if omitted
        name_sort: sort by name instead of source position
    """
    class _TestLoader(TestLoader):
        def __init__(self):
            super().__init__()
            self.sortTestMethodsUsing = self.compare_names
            self.testCaseClass: type[TestCase] | None = None

        # noinspection PyPep8Naming
        def loadTestsFromTestCase(self, testCaseClass: type[TestCase]) -> TestSuite:
            self.testCaseClass = testCaseClass
            return super().loadTestsFromTestCase(testCaseClass)

        def compare_names(self, name1: str, name2: str) -> int:
            if name_sort or self.testCaseClass is None:
                return (name1 > name2) - (name1 < name2)
            _lines, line_num1 = getsourcelines(getattr(self.testCaseClass, name1))
            _lines, line_num2 = getsourcelines(getattr(self.testCaseClass, name2))
            return line_num1 - line_num2

    check_folder_exists(runtime.paths.test)
    loader = _TestLoader()
    if tests:
        sys.path.append(str(runtime.paths.test))
        # Support test method name without class name, which unittest requires.
        unittest_names: list[str] = []
        for unittest_name in tests:
            parts = unittest_name.split('.')
            if len(parts) == 2:
                module_name, method_name = parts
                module = import_module(module_name)
                for member_name, member in module.__dict__.items():
                    if isclass(member) and issubclass(member, TestCase):
                        if hasattr(member, method_name):
                            unittest_names.append(
                                '.'.join([module_name, member.__name__, method_name]))
                            break
                else:
                    log_error(f'Failed to find unittest in {module_name}: {method_name}')
            else:
                unittest_names.append(unittest_name)
        suites = loader.loadTestsFromNames(unittest_names)
        sys.path = sys.path[:-1]
    else:
        suites = loader.discover(str(runtime.paths.test))
    if not suites:
        runtime.abort('No tests to run.')
    test_runner = TextTestRunner(verbosity=2 if runtime.options.verbose else 1)
    for suite in suites:
        test_runner.run(suite)
