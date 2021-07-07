"""Jiig top level task imports."""

import jiig

from . import alias, help, pdoc, task, tool, unittest, venv


@jiig.task(
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
def root(_runtime: jiig.Runtime):
    pass
