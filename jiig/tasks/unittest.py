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

"""
Jiig task that can run unit tests.
"""

import os
import unittest
from glob import glob

import jiig
from jiig.util.filesystem import check_folder_exists
from jiig.util.python import import_module_path


# TODO: Support tool tests, e.g. with TOOL specifier option.

@jiig.task
def unittest(
    runtime: jiig.Runtime,
    tests: jiig.fields.text(repeat=(None, None)),
):
    """
    Run unit tests using Python standard library unittest module.

    :param runtime: jiig Runtime API.
    :param tests: Test names to run, or all tests if omitted.
    """
    check_folder_exists(runtime.paths.test)
    module_map = {
        os.path.splitext(os.path.basename(file_path))[0]: file_path
        for file_path in glob(os.path.join(runtime.paths.test, 'test*.py'))
    }
    module_names_to_run = []
    if tests:
        for module_name in tests:
            if module_name in module_map:
                module_names_to_run.append(module_name)
            else:
                runtime.error(f'Ignoring unknown test module "{module_name}".')
    else:
        module_names_to_run.extend(module_map.keys())
    if not module_names_to_run:
        runtime.abort('No test suites found.')
    test_suites = []
    for module_name in module_names_to_run:
        test_module = import_module_path(module_map[module_name], module_name=module_name)
        test_suites.append(unittest.defaultTestLoader.loadTestsFromModule(test_module))
    test_runner = unittest.TextTestRunner()
    for test_suite in test_suites:
        test_runner.run(test_suite)
