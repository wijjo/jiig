"""Jiig task sub-task imports."""

import jiig

from . import create


@jiig.task(
    tasks={
        'create': create,
    }
)
def root(_runtime: jiig.Runtime):
    """Manage task modules."""
    pass
