"""
Alias rename task.
"""

import jiig


class Task(jiig.Task):
    """Rename alias."""

    alias: jiig.f.text('Existing alias name.')
    alias_new: jiig.f.text('New alias name.')

    def on_run(self, runtime: jiig.Runtime):
        with runtime.open_alias_catalog() as catalog:
            catalog.rename_alias(self.alias, self.alias_new)
