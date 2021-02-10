"""
Help task.
"""

from typing import List, Text

import jiig


TASK = jiig.Task(
    description='Display help screen.',
    args={
        'ALL_TASKS[!]': ('-a', '--all', 'Show all tasks, including hidden ones.'),
        'HELP_NAMES[*]': 'Command task name(s) or empty for top level help.',
    },
)


# For type inspection only.
class Data:
    ALL_TASKS: bool
    HELP_NAMES: List[Text]


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    help_text = runner.format_help(*data.HELP_NAMES, show_hidden=data.ALL_TASKS)
    if help_text:
        print(help_text)
