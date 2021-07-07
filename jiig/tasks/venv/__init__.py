"""Jiig venv sub-task imports."""

import jiig

from . import build, ipython, pip, python, run, update


@jiig.task(
    tasks={
        'build': build,
        'ipython': ipython,
        'pip': pip,
        'python': python,
        'run': run,
        'update': update,
    },
)
def root(runtime: jiig.Runtime):
    """Manage the tool virtual environment."""
    if not runtime.tool.pip_packages and not runtime.tool.tool_options.venv_required:
        runtime.abort(f'A virtual environment is not required.')
    if not runtime.tool.venv_folder:
        runtime.abort(f'Virtual environment folder (venv_folder) is not set.')
