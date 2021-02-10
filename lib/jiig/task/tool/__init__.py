"""
Jiig tool creation task.
"""

__all__ = ['project', 'script']

import os

import jiig
from jiig.util.console import abort

from . import project, script


TASK = jiig.Task(
    description='Manage tool assets.',
    tasks={
        'project': project,
        'script': script,
    },
)


@TASK.run
def task_run(runner: jiig.Runner, _data: object):
    if os.getcwd() == runner.tool.jiig_root_folder:
        abort('Please run this command from an application folder.')
