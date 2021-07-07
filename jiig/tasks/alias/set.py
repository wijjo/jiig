"""
Alias set task.
"""

import jiig


@jiig.task
def set_(
    runtime: jiig.Runtime,
    description: jiig.f.text('New alias description.',
                             cli_flags=('-d', '--description')),
    alias: jiig.f.text('Name of alias to create or update.'),
    command: jiig.f.text('Aliased command name.'),
    command_arguments: jiig.f.text('Aliased command arguments.',
                                   cli_trailing=True),
):
    """Create or update alias."""
    with runtime.open_alias_catalog() as catalog:
        if catalog.get_alias(alias):
            catalog.update_alias(alias,
                                 command=[command] + command_arguments,
                                 description=description)
        else:
            catalog.create_alias(alias,
                                 [command] + command_arguments,
                                 description=description)
