"""
Virtual environment general command execution task.
"""

import os
from typing import Text

import jiig
from jiig.util.console import abort


TASK = jiig.Task(
    description='Run miscellaneous command from virtual environment.',
    args={
        'COMMAND': 'Virtual environment command',
    },
    receive_trailing_arguments=True,
)


class Data:
    COMMAND: Text


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    command_path = runner.expand_path_template(f'{{VENV_FOLDER}}/bin/{data.COMMAND}')
    if not os.path.isfile(command_path):
        abort(f'Command "{data.COMMAND}" does not exist in virtual environment.')
    os.execl(command_path, command_path, *runner.trailing_arguments)
