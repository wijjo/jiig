"""
Virtual environment Python  execution task.
"""

import os

import jiig


@jiig.task(
    cli={
        'trailing': 'trailing_arguments',
    },
)
def python(
    runtime: jiig.Runtime,
    trailing_arguments: jiig.f.text(),
):
    """
    Run python from virtual environment.

    :param runtime: jiig Runtime API.
    :param trailing_arguments: Trailing CLI arguments.
    """
    python_path = runtime.format_path('{venv_folder}/bin/python')
    env = {'PYTHONPATH': os.path.pathsep.join(runtime.tool.library_folders)}
    os.execle(python_path, python_path, *trailing_arguments, env)
