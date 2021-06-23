"""
Alias description task.
"""

import jiig


class Task(jiig.Task):
    """Set alias description."""

    alias: jiig.f.text('Target alias name for description.')
    description: jiig.f.text('Alias description.')

    def on_run(self, runtime: jiig.Runtime):
        with runtime.open_alias_catalog() as catalog:
            description_text = ' '.join(self.description)
            catalog.update_alias(self.alias, description=description_text)
