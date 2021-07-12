"""Jiig top level task imports."""

import jiig

from . import alias, generate, help, pdoc, unittest, venv


@jiig.task(tasks=(generate, venv),
           secondary=(alias, help, pdoc),
           hidden=(unittest,))
def root(_runtime: jiig.Runtime):
    pass
