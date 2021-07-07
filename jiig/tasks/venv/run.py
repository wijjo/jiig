"""
Virtual environment general command execution task.
"""

import os

import jiig


@jiig.task
def run(
    runtime: jiig.Runtime,
    command: jiig.f.text('Virtual environment command'),
    trailing_arguments: jiig.f.text('Trailing CLI arguments.', cli_trailing=True),
):
    """Run miscellaneous command from virtual environment."""
    command_path = runtime.format_path(f'{{venv_folder}}/bin/{command}')
    if not os.path.isfile(command_path):
        runtime.abort(f'Command "{command}" does not exist in virtual environment.')
    os.execl(command_path, command_path, *trailing_arguments)
