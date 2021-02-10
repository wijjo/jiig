"""
Alias sub-command tasks.
"""

from typing import Text

import jiig


TASK = jiig.Task(
    description='Delete alias.',
    args={
        'ALIAS': 'Name of alias to delete.',
    },
)


# For type inspection only.
class Data:
    ALIAS: Text


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    with runner.open_alias_catalog() as catalog:
        catalog.delete_alias(data.ALIAS)
