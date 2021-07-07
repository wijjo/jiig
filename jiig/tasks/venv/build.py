"""
Virtual environment build sub-task.
"""

import jiig
from jiig.util.python import build_virtual_environment


@jiig.task
def build(
    runtime: jiig.Runtime,
    rebuild_venv: jiig.f.boolean('Force virtual environment rebuild.',
                                 cli_flags=('-r', '--rebuild')),
):
    """(Re-)Build the tool virtual environment."""
    runtime.heading(1, 'Build virtual environment')
    build_virtual_environment(runtime.tool.venv_folder,
                              packages=runtime.tool.pip_packages,
                              rebuild=rebuild_venv,
                              quiet=False)
