"""Jiig top level task imports."""

import jiig

from . import alias, help, pdoc, task, tool, unittest, venv


@jiig.task(tasks=(task, tool, venv),
           secondary=(alias, help, pdoc),
           hidden=(unittest,))
def root(_runtime: jiig.Runtime):
    pass
