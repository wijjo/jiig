"""Jiig task sub-task imports."""

import jiig

from . import create


# noinspection PyUnusedLocal
@jiig.task(tasks=(create,))
def root(runtime: jiig.Runtime):
    """
    Manage task modules.

    :param runtime: Jiig runtime API.
    """
    pass
