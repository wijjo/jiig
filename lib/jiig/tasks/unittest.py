"""Jiig task that can run unit tests."""

import os
import unittest
from glob import glob

from jiig import task, TaskRunner
from jiig.internal import global_data
from jiig.utility.console import abort, log_error
from jiig.utility.filesystem import check_folder_exists
from jiig.utility.python import import_module_path


# TODO: Support tool tests, e.g. with TOOL specifier option.
@task(
    name='unittest',
    help='run unit tests using Python standard library unittest module',
    arguments=[
        {
            'dest': 'TESTS',
            'nargs': '*',
            'help': 'unit test module name(s) to load and run (default: all)'
        },
    ],
    hidden_task=True)
def task_unittest(runner: TaskRunner):
    test_root = runner.params.TEST_ROOT or global_data.default_test_folder
    check_folder_exists(test_root)
    module_map = {
        os.path.splitext(os.path.basename(file_path))[0]: file_path
        for file_path in glob(os.path.join(test_root, 'test*.py'))
    }
    module_names_to_run = []
    if runner.args.TESTS:
        for module_name in runner.args.TESTS:
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
