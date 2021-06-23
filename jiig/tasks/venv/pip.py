"""
Virtual environment Pip execution task.
"""

import os

import jiig


class Task(jiig.Task):
    """Run pip from virtual environment."""

    trailing_arguments: jiig.f.text('Trailing CLI arguments.', cli_trailing=True)

    def on_run(self, runtime: jiig.Runtime):
        pip_path = runtime.format_path('{venv_folder}/bin/pip')
        os.execl(pip_path, pip_path, *self.trailing_arguments)
