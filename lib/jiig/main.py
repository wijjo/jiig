"""
Main CLI module.

Responsible for building the command line parser, parsing command line
arguments, and invoking task functions.
"""

import sys
import os

from . import constants, init_file, utility, parser, runner


def main(params: init_file.ParamData):
    if not params.LIB_FOLDERS:
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
    for lib_folder in reversed(params.LIB_FOLDERS):
        sys.path.insert(0, lib_folder)
    # Pull in all task modules in marked task folders to register mapped tasks.
    for lib_folder in params.LIB_FOLDERS:
        for package_folder, sub_folders, file_names in os.walk(lib_folder):
            # For now tasks file just serves as a simple marker for a tasks folder.
            if os.path.exists(os.path.join(package_folder, constants.TASKS_FILE)):
                # Base the package name on the sub-folder relative path.
                rel_sub_folder = package_folder[len(lib_folder) + 1:]
                package_name = '.'.join(rel_sub_folder.split(os.path.sep))
                utility.import_modules_from_folder(package_name, package_folder, retry=True)
    # Make sure a runner factory was registered.
    if not runner.RUNNER_FACTORY:
        utility.abort('No @runner_factory was registered.')
    # Parse the command line and tweak global options and environment variables.
    cli_parser = parser.CommandLineParser()
    cli_results = cli_parser.parse(description='Execute application build/run tasks.')
    try:
        for task_idx, execution_task in enumerate(cli_results.mapped_task.execution_tasks):
            task_runner = runner.RUNNER_FACTORY(
                runner.RunnerData(cli_results.args,
                                  cli_results.help_formatters,
                                  PRIMARY_TASK=False,
                                  **params))
            execution_task.task_function(task_runner)
        task_runner = runner.RUNNER_FACTORY(
            runner.RunnerData(cli_results.args,
                              cli_results.help_formatters,
                              PRIMARY_TASK=True,
                              **params))
        cli_results.mapped_task.task_function(task_runner)
    except RuntimeError as exc:
        print(exc)
        print(cli_results.args)
    except KeyboardInterrupt:
        print('')
