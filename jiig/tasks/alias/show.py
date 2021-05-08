"""
Show alias(es) task.
"""

import jiig
from jiig.util.console import log_error, log_message


class Task(jiig.Task):
    """Display alias(es)."""

    aliases: jiig.text('Alias name(s) to display.', repeat=(1, None))

    def on_run(self, runtime: jiig.Runtime):
        """
        Override-able method that gets called to run task logic.

        :param runtime: runtime data and API
        """
        with runtime.open_alias_catalog() as catalog:
            for name in self.aliases:
                resolved_alias = catalog.get_alias(name)
                if resolved_alias is not None:
                    log_message(resolved_alias)
                else:
                    log_error(f'Alias "{name}" does not exist.')
