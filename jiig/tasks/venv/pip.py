"""
Virtual environment Pip execution task.
"""

import os

import jiig


class Task(jiig.Task):
    """Run pip from virtual environment."""

    trailing_arguments: jiig.text('Trailing CLI arguments.', cli_trailing=True)

    def on_run(self, runtime: jiig.Runtime):
        pip_path = runtime.expand_path_template('{VENV_FOLDER}/bin/pip')
        os.execl(pip_path, pip_path, *self.trailing_arguments)
