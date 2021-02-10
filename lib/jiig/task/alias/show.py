"""
Alias show task.
"""

from typing import Text, List

import jiig
from jiig.util.console import log_error, log_message


TASK = jiig.Task(
    description='Display alias.',
    args={
        'ALIASES[+]': 'Alias name(s) to display.',
    },
)


# For type inspection only.
class Data:
    ALIASES: List[Text]


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    with runner.open_alias_catalog() as catalog:
        for name in data.ALIASES:
            resolved_alias = catalog.get_alias(name)
            if resolved_alias is not None:
                log_message(resolved_alias)
            else:
                log_error(f'Alias "{name}" does not exist.')
