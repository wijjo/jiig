"""
Jiig task creation task.
"""

__all__ = ['create']

import jiig

from . import create


TASK = jiig.Task(
    description='Manage task modules.',
    tasks={
        'create': create,
    },
)
