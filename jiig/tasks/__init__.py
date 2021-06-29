"""Jiig top level task imports."""

import jiig

from . import alias, help, pdoc, task, tool, unittest, venv


class Task(
    jiig.Task,
    tasks={
        'task': task,
        'tool': tool,
        'venv': venv,
        'alias[s]': alias,
        'help[s]': help,
        'pdoc[s]': pdoc,
        'unittest[h]': unittest,
    },
):
    pass
