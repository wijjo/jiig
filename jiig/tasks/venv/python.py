"""
Virtual environment Python  execution task.
"""

import os

import jiig


@jiig.task
def python(
    runtime: jiig.Runtime,
    trailing_arguments: jiig.f.text('Trailing CLI arguments.', cli_trailing=True),
):
    """Run python from virtual environment."""
    python_path = runtime.format_path('{venv_folder}/bin/python')
    env = {'PYTHONPATH': os.path.pathsep.join(runtime.tool.library_folders)}
    os.execle(python_path, python_path, *trailing_arguments, env)
