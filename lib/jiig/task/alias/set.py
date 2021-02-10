"""
Alias set task.
"""

from typing import Text, Optional

import jiig


TASK = jiig.Task(
    description='Create or update alias.',
    args={
        'DESCRIPTION': ('-d', '--description', 'New alias description.'),
        'ALIAS': 'Name of alias to create or update.',
        'COMMAND': 'Command with options and arguments.',
    },
    # The command to alias is fed as unparsed trailing arguments.
    receive_trailing_arguments=True,
)


# For type inspection only.
class Data:
    DESCRIPTION: Optional[Text]
    ALIAS: Text
    COMMAND: Text


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    with runner.open_alias_catalog() as catalog:
        if catalog.get_alias(data.ALIAS):
            catalog.update_alias(data.ALIAS,
                                 command=[data.COMMAND] + runner.trailing_arguments,
                                 description=data.DESCRIPTION)
        else:
            catalog.create_alias(data.ALIAS,
                                 [data.COMMAND] + runner.trailing_arguments,
                                 description=data.DESCRIPTION)
