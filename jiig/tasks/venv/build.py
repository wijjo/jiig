"""
Virtual environment build sub-task.
"""

import jiig
from jiig.util.python import build_virtual_environment


@jiig.task(
    cli={
        'options': {
            'rebuild_venv': ('-r', '--rebuild'),
        }
    }
)
def build(
    runtime: jiig.Runtime,
    rebuild_venv: jiig.f.boolean(),
):
    """
    (Re-)Build the tool virtual environment.

    :param runtime: Jiig runtime API.
    :param rebuild_venv: Force virtual environment rebuild.
    """
    runtime.heading(1, 'Build virtual environment')
    build_virtual_environment(runtime.tool.venv_folder,
                              packages=runtime.tool.pip_packages,
                              rebuild=rebuild_venv,
                              quiet=False)
