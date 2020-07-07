"""
Main CLI module.

Responsible for building the command line parser, parsing command line
arguments, and invoking task functions.
"""

import sys
import os
from typing import Dict, Text, List

from . import constants, init_file, utility, parser, runner


def main(all_params_in: Dict, tool_params_in: Dict):
    # all_params incorporates tool_params data, but need tool_params separately
    # for task inheritance checks.
    all_params = init_file.ParamData(all_params_in)
    tool_params = init_file.ParamData(tool_params_in)
    if not all_params.LIB_FOLDERS:
        utility.abort('No library folders are specified.')
    # Peek at global options so that debug/verbose modes can be enabled during actual parsing.
    global_args = parser.pre_parse_global_args()
    if global_args.VERBOSE:
        # Dry-run implies verbose.
        constants.VERBOSE = global_args.VERBOSE or global_args.DRY_RUN
    if global_args.DEBUG:
        constants.DEBUG = global_args.DEBUG
    if global_args.DRY_RUN:
        constants.DRY_RUN = global_args.DRY_RUN
    # Adjust the Python system path to be able to find app modules.
    for lib_folder in reversed(all_params.LIB_FOLDERS):
        sys.path.insert(0, lib_folder)
    # Pull in all task modules in marked task folders to register mapped tasks.
    task_folders: List[Text] = []
    for lib_folder in all_params.LIB_FOLDERS:
        for module_path in utility.import_modules_from_folder(
                lib_folder, retry=True, marker=constants.TASKS_FILE):
            task_folder = os.path.dirname(module_path)
            if task_folder not in task_folders:
                task_folders.append(task_folder)
    all_params['TASK_FOLDERS'] = task_folders
    # Make sure a runner factory was registered.
    if not runner.RUNNER_FACTORY:
        utility.abort('No @runner_factory was registered.')
    # Parse the command line and tweak global options and environment variables.
    cli_parser = parser.CommandLineParser(tool_params.LIB_FOLDERS)
    cli_results = cli_parser.parse(description=tool_params.TOOL_DESCRIPTION)
    try:
        for task_idx, execution_task in enumerate(cli_results.mapped_task.execution_tasks):
            task_runner = runner.RUNNER_FACTORY(
                runner.RunnerData(cli_results.args,
                                  cli_results.help_formatters,
                                  PRIMARY_TASK=False,
                                  **all_params))
            execution_task.task_function(task_runner)
        task_runner = runner.RUNNER_FACTORY(
            runner.RunnerData(cli_results.args,
                              cli_results.help_formatters,
                              PRIMARY_TASK=True,
                              **all_params))
        cli_results.mapped_task.task_function(task_runner)
    except RuntimeError as exc:
        print(exc)
        print(cli_results.args)
    except KeyboardInterrupt:
        print('')
