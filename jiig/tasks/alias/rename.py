"""
Alias rename task.
"""

import jiig


@jiig.task
def rename(
    runtime: jiig.Runtime,
    alias: jiig.f.text(),
    alias_new: jiig.f.text(),
):
    """
    Rename alias.

    :param runtime: Jiig runtime API.
    :param alias: Existing alias name.
    :param alias_new: New alias name.
    """
    with runtime.open_alias_catalog() as catalog:
        catalog.rename_alias(alias, alias_new)
