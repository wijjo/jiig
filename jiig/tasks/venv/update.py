"""
Virtual environment update task.
"""

import jiig
from jiig.util.console import log_heading
from jiig.util.python import update_virtual_environment


class Task(jiig.Task):
    """Delete the tool virtual environment."""

    def on_run(self, runtime: jiig.Runtime):
        if not runtime.is_secondary:
            log_heading(1, 'Delete virtual environment')
        update_virtual_environment(runtime.tool.venv_folder, packages=runtime.tool.pip_packages)
