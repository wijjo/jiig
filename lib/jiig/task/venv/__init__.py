"""
Jiig virtual environment root task.
"""

__all__ = ['build', 'ipython', 'pip', 'python', 'run', 'update']

import jiig
from jiig.util.console import abort

from . import build, ipython, pip, python, run, update


TASK = jiig.Task(
    description='Manage the tool virtual environment.',
    tasks={
        'build': build,
        'ipython': ipython,
        'pip': pip,
        'python': python,
        'run': run,
        'update': update,
    }
)


@TASK.run
def task_run(runner: jiig.Runner, _data: object):
    if not runner.tool.pip_packages and not runner.tool.options.venv_required:
        abort(f'A virtual environment is not required.')
    if not runner.tool.venv_folder:
        abort(f'Virtual environment folder (venv_folder) is not set.')
