"""
Virtual environment update task.
"""

import jiig
from jiig.util.console import log_heading
from jiig.util.python import update_virtual_environment


TASK = jiig.Task(
    description='Delete the tool virtual environment.',
)


@TASK.run
def task_run(runner: jiig.Runner, _data):
    if not runner.is_secondary:
        log_heading(1, 'Delete virtual environment')
    update_virtual_environment(runner.tool.venv_folder, packages=runner.tool.pip_packages)
