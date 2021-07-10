"""
Alias sub-command tasks.
"""

import jiig


@jiig.task
def delete(
    runtime: jiig.Runtime,
    alias: jiig.f.text(),
):
    """
    Delete alias.

    :param runtime: Jiig runtime API.
    :param alias: Name of alias to delete.
    """
    with runtime.open_alias_catalog() as catalog:
        catalog.delete_alias(alias)
