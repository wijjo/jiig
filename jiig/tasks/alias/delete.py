"""
Alias sub-command tasks.
"""

import jiig


@jiig.task
def delete(
    runtime: jiig.Runtime,
    alias: jiig.f.text('Name of alias to delete.'),
):
    """Delete alias."""
    with runtime.open_alias_catalog() as catalog:
        catalog.delete_alias(alias)
