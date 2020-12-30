"""
Help task.
"""

import jiig


class TaskClass(jiig.Task):
    """Display help screen."""

    opts = [
        jiig.BoolOpt(('-a', '--all'), 'ALL_TASKS',
                     'Show all tasks, including hidden ones.'),
    ]
    args = [
        jiig.Arg('HELP_NAMES',
                 'Command task name(s) or empty for top level help.',
                 cardinality='*'),
    ]

    def on_run(self):
        help_text = self.format_help(*self.data.HELP_NAMES,
                                     show_hidden=self.data.ALL_TASKS)
        if help_text:
            print(help_text)
