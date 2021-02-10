"""
Alias description task.
"""

from typing import Text

import jiig


TASK = jiig.Task(
    description='Set alias description.',
    args={
        'ALIAS': 'Target alias name for description.',
        'DESCRIPTION': 'Alias description.',
    },
)


# For type inspection only.
class Data:
    ALIAS: Text
    DESCRIPTION: Text


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    with runner.open_alias_catalog() as catalog:
        description_text = ' '.join(data.DESCRIPTION)
        catalog.update_alias(data.ALIAS, description=description_text)
