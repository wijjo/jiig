"""
Jiig alias sub-task imports.
"""

import jiig

from . import delete, description, list, rename, set, show


# noinspection PyUnusedLocal
@jiig.task(tasks=(delete, description, list, rename, set, show))
def root(runtime: jiig.Runtime):
    """
    Alias management tasks.

    :param runtime: Jiig runtime API.
    """
    pass
