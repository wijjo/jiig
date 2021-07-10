"""
Virtual environment Pip execution task.
"""

import os

import jiig


@jiig.task(
    cli={
        'trailing': 'trailing_arguments',
    },
)
def pip(
    runtime: jiig.Runtime,
    trailing_arguments: jiig.f.text(),
):
    """
    Run pip from virtual environment.

    :param runtime: jiig Runtime API.
    :param trailing_arguments: Trailing CLI arguments.
    """
    pip_path = runtime.format_path('{venv_folder}/bin/pip')
    os.execl(pip_path, pip_path, *trailing_arguments)
