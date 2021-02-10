"""
Jiig alias root task.
"""

__all__ = ['delete', 'description', 'list', 'rename', 'set', 'show']

from jiig import model

from . import delete, description, list, rename, set, show


TASK = model.Task(
    description='Alias management tasks.',
    tasks={
        'delete': delete,
        'description': description,
        'list': list,
        'rename': rename,
        'set': set,
        'show': show,
    },
)
