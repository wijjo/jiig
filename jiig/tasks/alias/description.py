"""
Alias description task.
"""

import jiig


@jiig.task
def description_(
    runtime: jiig.Runtime,
    alias: jiig.f.text(),
    description: jiig.f.text(),
):
    """
    Set alias description.

    :param runtime: Jiig runtime API.
    :param alias: Target alias name for description.
    :param description: Alias description.
    """
    with runtime.open_alias_catalog() as catalog:
        description_text = ' '.join(description)
        catalog.update_alias(alias, description=description_text)
