"""
Jiig root task.
"""

import jiig

from . import task, tool, venv, alias, help, pdoc, unittest


TASK = jiig.Task(
    tasks={
        'task': task,
        'tool': tool,
        'venv': venv,
        'alias[s]': alias,
        'help[s]': help,
        'pdoc[s]': pdoc,
        'unittest[h]': unittest,
    },
)
