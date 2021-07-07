"""
Alias description task.
"""

import jiig


@jiig.task
def description_(
    runtime: jiig.Runtime,
    alias: jiig.f.text('Target alias name for description.'),
    description: jiig.f.text('Alias description.'),
):
    """Set alias description."""
    with runtime.open_alias_catalog() as catalog:
        description_text = ' '.join(description)
        catalog.update_alias(alias, description=description_text)
