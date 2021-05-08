"""
Virtual environment build sub-task.
"""

import jiig
from jiig.util.console import log_heading
from jiig.util.python import build_virtual_environment


class Task(jiig.Task):
    """(Re-)Build the tool virtual environment."""

    rebuild_venv: jiig.boolean('Force virtual environment rebuild.', cli_flags=('-r', '--rebuild'))

    def on_run(self, runtime: jiig.Runtime):
        if not runtime.is_secondary:
            log_heading(1, 'Build virtual environment')
        build_virtual_environment(runtime.tool.venv_folder,
                                  packages=runtime.tool.pip_packages,
                                  rebuild=self.rebuild_venv,
                                  quiet=runtime.is_secondary)
