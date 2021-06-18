"""
Virtual environment general command execution task.
"""

import os

import jiig
from jiig.util.console import abort


class Task(jiig.Task):
    """Run miscellaneous command from virtual environment."""

    command: jiig.text('Virtual environment command')
    trailing_arguments: jiig.text('Trailing CLI arguments.', cli_trailing=True)

    def on_run(self, runtime: jiig.Runtime):
        command_path = runtime.format_path(f'{{venv_folder}}/bin/{self.command}')
        if not os.path.isfile(command_path):
            abort(f'Command "{self.command}" does not exist in virtual environment.')
        os.execl(command_path, command_path, *self.trailing_arguments)
