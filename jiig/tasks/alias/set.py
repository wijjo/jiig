"""
Alias set task.
"""

import jiig


@jiig.task(
    cli={
        'options': {
            'description': ('-d', '--description'),
        },
        'trailing': 'command_arguments',
    },
)
def set_(
    runtime: jiig.Runtime,
    description: jiig.f.text(),
    alias: jiig.f.text(),
    command: jiig.f.text(),
    command_arguments: jiig.f.text(repeat=(1, None)),
):
    """
    Create or update alias.

    :param runtime: jiig Runtime API.
    :param description: New alias description.
    :param alias: Name of alias to create or update.
    :param command: Aliased command name.
    :param command_arguments: Aliased command arguments.
    """
    with runtime.open_alias_catalog() as catalog:
        if catalog.get_alias(alias):
            catalog.update_alias(alias,
                                 command=[command] + command_arguments,
                                 description=description)
        else:
            catalog.create_alias(alias,
                                 [command] + command_arguments,
                                 description=description)
