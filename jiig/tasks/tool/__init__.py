"""Jiig tool sub-task imports."""

import os
import jiig

from . import project, script


@jiig.task(
    tasks={
        'project': project,
        'script': script,
    },
)
def root(runtime: jiig.Runtime):
    """Manage tool assets."""
    if os.getcwd() == runtime.tool.jiig_root_folder:
        runtime.abort('Please run this command from an application folder.')
