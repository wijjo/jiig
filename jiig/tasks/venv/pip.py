"""
Virtual environment Pip execution task.
"""

import os

import jiig


@jiig.task
def pip(
    runtime: jiig.Runtime,
    trailing_arguments: jiig.f.text('Trailing CLI arguments.', cli_trailing=True),
):
    """Run pip from virtual environment."""
    pip_path = runtime.format_path('{venv_folder}/bin/pip')
    os.execl(pip_path, pip_path, *trailing_arguments)
