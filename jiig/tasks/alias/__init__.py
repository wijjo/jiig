"""Jiig alias sub-task imports."""

import jiig

from . import delete, description, list, rename, set, show


@jiig.task(
    tasks={
        'delete': delete,
        'description': description,
        'list': list,
        'rename': rename,
        'set': set,
        'show': show,
    },
)
def root(_runtime: jiig.Runtime):
    """Alias management tasks."""
    pass
