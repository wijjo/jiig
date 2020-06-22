"""
Main CLI module.

Responsible for building the command line parser, parsing command line
arguments, and invoking task functions.
"""

from typing import Text, Dict, List


def main(app_name: Text,
         base_folder: Text,
         venv_folder: Text,
         task_packages: Dict[Text, Text],
         pip_packages: List[Text]):
    # Delay these imports until the actual call to main() in case this module is
    # loaded outside of the virtual environment and doesn't have all library
    # dependencies available.
    from . import parser, runner, utility
    # Pull in all task modules in task folders to register mapped tasks.
    for package_name, package_folder in task_packages.items():
        utility.import_modules_from_folder(package_name, package_folder, retry=True)
    # Parse the command line and tweak global options and environment variables.
    cli = parser.CommandLineParser()
    cli.parse()
    if cli.args.VERBOSE:
        utility.VERBOSE = cli.args.VERBOSE
    params = dict(APP_NAME=app_name,
                  BASE_FOLDER=base_folder,
                  VENV_FOLDER=venv_folder,
                  PIP_PACKAGES=pip_packages)
    try:
        for task_idx, execution_task in enumerate(cli.mapped_task.execution_tasks):
            task_runner = runner.TaskRunner(cli.args,
                                            cli.help_formatters,
                                            PRIMARY_TASK=False,
                                            **params)
            execution_task.task_function(task_runner)
        task_runner = runner.TaskRunner(cli.args,
                                        cli.help_formatters,
                                        PRIMARY_TASK=True,
                                        **params)
        cli.mapped_task.task_function(task_runner)
    except RuntimeError as exc:
        print(exc)
        print(cli.args)
    except KeyboardInterrupt:
        print('')
