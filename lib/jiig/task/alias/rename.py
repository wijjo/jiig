"""
Alias rename task.
"""

from typing import Text

import jiig


TASK = jiig.Task(
    description='Rename alias.',
    args={
        'ALIAS': 'Existing alias name.',
        'ALIAS_NEW': 'New alias name.',
    },
)


# For type inspection only.
class Data:
    ALIAS: Text
    ALIAS_NEW: Text


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    with runner.open_alias_catalog() as catalog:
        catalog.rename_alias(data.ALIAS, data.ALIAS_NEW)
