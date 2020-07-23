"""
Main CLI module.

Responsible for building the command line parser, parsing command line
arguments, and invoking task functions.
"""

import sys
import os
from typing import Dict, Text, List

from . import constants, init_file, utility, parser, runner


def main(all_params: Dict, tool_params: Dict = None):
    # all_params incorporates tool_params data, but need tool_params separately
    # for task inheritance checks.
    if tool_params is None:
        tool_params = dict(all_params)
    all_params_obj = init_file.ParamData(all_params)
    tool_params_obj = init_file.ParamData(tool_params)
    if not all_params_obj.LIB_FOLDERS:
        utility.abort('No library folders are specified.')
    # Peek at global options so that debug/verbose modes can be enabled during
    # actual parsing.
    global_args = parser.pre_parse_global_args()
    if global_args.VERBOSE:
        # Dry-run implies verbose.
        constants.VERBOSE = global_args.VERBOSE or global_args.DRY_RUN
    if global_args.DEBUG:
        constants.DEBUG = global_args.DEBUG
    if global_args.DRY_RUN:
        constants.DRY_RUN = global_args.DRY_RUN
    # Adjust the Python system path to be able to find app modules.
    for lib_folder in reversed(all_params_obj.LIB_FOLDERS):
        sys.path.insert(0, lib_folder)
    # Pull in all task modules in marked task folders to register mapped tasks.
    task_folders: List[Text] = []
    for lib_folder in all_params_obj.TASK_FOLDERS:
        for module_path in utility.import_modules_from_folder(lib_folder, retry=True):
            task_folder = os.path.dirname(module_path)
            if task_folder not in task_folders:
                task_folders.append(task_folder)
    all_params_obj['TASK_FOLDERS'] = task_folders
    # Add the `help` task.
    from . import help_task     # noqa
    runner_factory = runner.RUNNER_FACTORY
    if not runner_factory:
        def _default_runner_factory(data: runner.RunnerData) -> runner.TaskRunner:
            return runner.TaskRunner(data)
        runner_factory = _default_runner_factory
    # Parse the command line and tweak global options and environment variables.
    cli_parser = parser.CommandLineParser(tool_params_obj.TASK_FOLDERS)
    cli_results = cli_parser.parse(description=tool_params_obj.TOOL_DESCRIPTION)
    try:
        for task_idx, execution_task in enumerate(cli_results.mapped_task.execution_tasks):
            task_runner = runner_factory(
                runner.RunnerData(cli_results.args,
                                  cli_results.help_formatters,
                                  PRIMARY_TASK=False,
                                  **all_params_obj))
            execution_task.task_function(task_runner)
        task_runner = runner_factory(
            runner.RunnerData(cli_results.args,
                              cli_results.help_formatters,
                              PRIMARY_TASK=True,
                              **all_params_obj))
        cli_results.mapped_task.task_function(task_runner)
    except RuntimeError as exc:
        print(exc)
        print(cli_results.args)
    except KeyboardInterrupt:
        print('')
