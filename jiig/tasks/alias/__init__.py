"""
Jiig alias sub-task imports.
"""

import jiig

from . import delete, description, list, rename, set, show


# noinspection PyUnusedLocal
@jiig.task(tasks=(delete, description, list, rename, set, show))
def root(runtime: jiig.Runtime):
    """
    Create and manage task command aliases.

    :param runtime: Jiig runtime API.
    """
    pass
