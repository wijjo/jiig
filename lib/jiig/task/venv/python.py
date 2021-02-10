"""
Virtual environment Python  execution task.
"""

import os

import jiig


TASK = jiig.Task(
    description='Run python from virtual environment.',
    receive_trailing_arguments=True,
)


@TASK.run
def task_run(runner: jiig.Runner, _data):
    python_path = runner.expand_path_template('{VENV_FOLDER}/bin/python')
    env = {'PYTHONPATH': os.path.pathsep.join(runner.tool.library_folders)}
    os.execle(python_path, python_path, *runner.trailing_arguments, env)
