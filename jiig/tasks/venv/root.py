"""
Jiig virtual environment root task.
"""

import jiig
from jiig.util.console import abort

from . import build, ipython, pip, python, run, update


class Task(jiig.Task,
           tasks={'build': build,
                  'ipython': ipython,
                  'pip': pip,
                  'python': python,
                  'run': run,
                  'update': update},
           ):
    """Manage the tool virtual environment."""

    def on_run(self, runtime: jiig.Runtime):
        if not runtime.tool.pip_packages and not runtime.tool.options.venv_required:
            abort(f'A virtual environment is not required.')
        if not runtime.tool.venv_folder:
            abort(f'Virtual environment folder (venv_folder) is not set.')
