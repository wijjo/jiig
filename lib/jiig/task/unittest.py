"""
Jiig task that can run unit tests.
"""

import os
import unittest
from glob import glob
from typing import Text, List

import jiig
from jiig.util.console import abort, log_error
from jiig.util.filesystem import check_folder_exists
from jiig.util.python import import_module_path


# TODO: Support tool tests, e.g. with TOOL specifier option.
TASK = jiig.Task(
    description='Run unit tests using Python standard library unittest module.',
    args={
        'TESTS[*]': 'Unit test module name(s) to load/run (default: <all>).',
    },
)


# For type inspection only.
class Data:
    TESTS: List[Text]


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    check_folder_exists(runner.tool.test_folder)
    module_map = {
        os.path.splitext(os.path.basename(file_path))[0]: file_path
        for file_path in glob(os.path.join(runner.tool.test_folder, 'test*.py'))
    }
    module_names_to_run = []
    if data.TESTS:
        for module_name in data.TESTS:
            if module_name in module_map:
                module_names_to_run.append(module_name)
            else:
                log_error(f'Ignoring unknown test module "{module_name}".')
    else:
        module_names_to_run.extend(module_map.keys())
    if not module_names_to_run:
        abort('No test suites found.')
    test_suites = []
    for module_name in module_names_to_run:
        test_module = import_module_path(f'{module_name}', module_map[module_name])
        test_suites.append(unittest.defaultTestLoader.loadTestsFromModule(test_module))
    test_runner = unittest.TextTestRunner()
    for test_suite in test_suites:
        test_runner.run(test_suite)
