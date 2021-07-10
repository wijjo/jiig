"""
Show alias(es) task.
"""

import jiig


@jiig.task
def show(
    runtime: jiig.Runtime,
    aliases: jiig.f.text(repeat=(1, None)),
):
    """
    Display alias(es).

    :param runtime: jiig Runtime API.
    :param aliases: Alias name(s) to display.
    """
    with runtime.open_alias_catalog() as catalog:
        for name in aliases:
            resolved_alias = catalog.get_alias(name)
            if resolved_alias is not None:
                runtime.message(resolved_alias)
            else:
                runtime.error(f'Alias "{name}" does not exist.')
