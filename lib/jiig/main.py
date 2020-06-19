"""
Main CLI module.

Responsible for building the command line parser, parsing command line
arguments, and invoking task functions.
"""

from typing import Text, Dict

from . import parser, runner, utility


def main(app_name: Text, base_folder: Text, task_packages: Dict[Text, Text]):
    # Pull in all task modules in task folders to register mapped tasks.
    for package_name, package_folder in task_packages.items():
        utility.import_modules_from_folder(package_name, package_folder)
    # Parse the command line and tweak global options and environment variables.
    cli = parser.CommandLineParser()
    cli.parse()
    if cli.args.VERBOSE:
        utility.VERBOSE = cli.args.VERBOSE
    params = dict(APP_NAME=app_name, BASE_FOLDER=base_folder)
    try:
        for execution_task in cli.mapped_task.execution_tasks:
            task_runner = runner.TaskRunner(cli.args, cli.help_formatters, **params)
            execution_task.task_function(task_runner)
        task_runner = runner.TaskRunner(cli.args, cli.help_formatters, **params)
        cli.mapped_task.task_function(task_runner)
    except RuntimeError as exc:
        print(exc)
        print(cli.args)
    except KeyboardInterrupt:
        print('')
