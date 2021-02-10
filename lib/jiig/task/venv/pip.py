"""
Virtual environment Pip execution task.
"""

import os

import jiig


TASK = jiig.Task(
    description='Run pip from virtual environment.',
    receive_trailing_arguments=True,
)


@TASK.run
def task_run(runner: jiig.Runner, _data):
    pip_path = runner.expand_path_template('{VENV_FOLDER}/bin/pip')
    os.execl(pip_path, pip_path, *runner.trailing_arguments)
