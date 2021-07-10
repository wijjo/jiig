"""
Virtual environment general command execution task.
"""

import os

import jiig


@jiig.task(
    cli={
        'trailing': 'trailing_arguments',
    },
)
def run(
    runtime: jiig.Runtime,
    command: jiig.f.text(),
    trailing_arguments: jiig.f.text(repeat=(None, None)),
):
    """
    Run miscellaneous command from virtual environment.

    :param runtime: jiig Runtime API.
    :param command: Virtual environment command.
    :param trailing_arguments: Trailing CLI arguments.
    """
    command_path = runtime.format_path(f'{{venv_folder}}/bin/{command}')
    if not os.path.isfile(command_path):
        runtime.abort(f'Command "{command}" does not exist in virtual environment.')
    os.execl(command_path, command_path, *trailing_arguments)
