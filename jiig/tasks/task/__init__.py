"""Jiig task sub-task imports."""

import jiig

from . import create


class Task(
    jiig.Task,
    tasks={
        'create': create,
    }
):
    """Manage task modules."""
    pass
