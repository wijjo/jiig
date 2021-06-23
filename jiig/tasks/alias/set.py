"""
Alias set task.
"""

import jiig


class Task(jiig.Task):
    """Create or update alias."""

    description: jiig.f.text('New alias description.',
                             cli_flags=('-d', '--description'))
    alias: jiig.f.text('Name of alias to create or update.')
    command: jiig.f.text('Aliased command name.')
    command_arguments: jiig.f.text('Aliased command arguments.',
                                   cli_trailing=True)

    def on_run(self, runtime: jiig.Runtime):
        with runtime.open_alias_catalog() as catalog:
            if catalog.get_alias(self.alias):
                catalog.update_alias(self.alias,
                                     command=[self.command] + self.command_arguments,
                                     description=self.description)
            else:
                catalog.create_alias(self.alias,
                                     [self.command] + self.command_arguments,
                                     description=self.description)
