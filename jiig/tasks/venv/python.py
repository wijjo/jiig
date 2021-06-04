"""
Virtual environment Python  execution task.
"""

import os

import jiig


class Task(jiig.Task):
    """Run python from virtual environment."""

    trailing_arguments: jiig.text('Trailing CLI arguments.', cli_trailing=True)

    def on_run(self, runtime: jiig.Runtime):
        python_path = runtime.format_path('{VENV_FOLDER}/bin/python')
        env = {'PYTHONPATH': os.path.pathsep.join(runtime.tool.library_folders)}
        os.execle(python_path, python_path, *self.trailing_arguments, env)
