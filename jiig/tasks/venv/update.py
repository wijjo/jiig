"""
Virtual environment update task.
"""

import jiig
from jiig.util.python import update_virtual_environment


@jiig.task
def update(runtime: jiig.Runtime):
    """Delete the tool virtual environment."""
    runtime.heading(1, 'Delete virtual environment')
    update_virtual_environment(runtime.tool.venv_folder, packages=runtime.tool.pip_packages)
