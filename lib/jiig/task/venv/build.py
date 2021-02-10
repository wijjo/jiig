"""
Virtual environment build sub-task.
"""

import jiig
from jiig.util.console import log_heading
from jiig.util.python import build_virtual_environment


TASK = jiig.Task(
    description='(Re-)Build the tool virtual environment.',
    args={
        'REBUILD_VENV[!]': ('-r', '--rebuild', 'Force virtual environment rebuild.'),
    }
)


# For type inspection only.
class Data:
    REBUILD_VENV: bool


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    if not runner.is_secondary:
        log_heading(1, 'Build virtual environment')
    build_virtual_environment(runner.tool.venv_folder,
                              packages=runner.tool.pip_packages,
                              rebuild=data.REBUILD_VENV,
                              quiet=runner.is_secondary)
