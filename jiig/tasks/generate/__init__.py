"""Jiig tool sub-task imports."""

import os
import jiig

from . import project, script, task


@jiig.task(tasks=(project, script, task))
def root(runtime: jiig.Runtime):
    """
    Manage tool assets.

    :param runtime: Jiig runtime API.
    """
    if os.getcwd() == runtime.tool.jiig_root_folder:
        runtime.abort('Please run this command from an application folder.')
