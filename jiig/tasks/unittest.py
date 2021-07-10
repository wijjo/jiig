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
    tests: jiig.f.text(repeat=(None, None)),
):
    """
    Run unit tests using Python standard library unittest module.

    :param runtime: jiig Runtime API.
    :param tests: Test names to run, or all tests if omitted.
    """
    check_folder_exists(runtime.tool.test_folder)
    module_map = {
        os.path.splitext(os.path.basename(file_path))[0]: file_path
        for file_path in glob(os.path.join(runtime.tool.test_folder, 'test*.py'))
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
