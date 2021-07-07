"""
Alias rename task.
"""

import jiig


@jiig.task
def rename(
    runtime: jiig.Runtime,
    alias: jiig.f.text('Existing alias name.'),
    alias_new: jiig.f.text('New alias name.'),
):
    """Rename alias."""
    with runtime.open_alias_catalog() as catalog:
        catalog.rename_alias(alias, alias_new)
