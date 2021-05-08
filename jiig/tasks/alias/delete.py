"""
Alias sub-command tasks.
"""

import jiig


class Task(jiig.Task):
    """Delete alias."""
    alias: jiig.text('Name of alias to delete.')

    def on_run(self, runtime: jiig.Runtime):
        with runtime.open_alias_catalog() as catalog:
            catalog.delete_alias(self.alias)
