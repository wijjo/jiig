"""
Help task.
"""

from typing import List, Text

import jiig


class TaskClass(jiig.Task):
    """Display help screen."""

    # For type inspection only.
    class Data:
        ALL_TASKS: bool
        HELP_NAMES: List[Text]
    data: Data

    args = {
        'ALL_TASKS!': ('-a', '--all', 'Show all tasks, including hidden ones.'),
        'HELP_NAMES[*]': 'Command task name(s) or empty for top level help.',
    }

    def on_run(self):
        help_text = self.format_help(*self.data.HELP_NAMES,
                                     show_hidden=self.data.ALL_TASKS)
        if help_text:
            print(help_text)
