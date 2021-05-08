"""
Jiig tool creation task.
"""

import os

import jiig
from jiig.util.console import abort

from . import project, script


class Task(jiig.Task,
           tasks={'project': project,
                  'script': script},
           ):
    """Manage tool assets."""

    def on_run(self, runtime: jiig.Runtime):
        if os.getcwd() == runtime.tool.jiig_root_folder:
            abort('Please run this command from an application folder.')
