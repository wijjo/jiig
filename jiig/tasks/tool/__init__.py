"""Jiig tool sub-task imports."""

import os
import jiig

from . import project, script


class Task(
    jiig.Task,
    tasks={
        'project': project,
        'script': script,
    },
):
    """Manage tool assets."""
    def on_run(self, runtime: jiig.Runtime):
        if os.getcwd() == runtime.tool.jiig_root_folder:
            jiig.util.log.abort('Please run this command from an application folder.')
