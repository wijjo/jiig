"""
Help task.
"""

import jiig


class Task(jiig.Task):
    """Display help screen."""

    all_tasks: jiig.f.boolean('Show all tasks, including hidden ones.',
                              cli_flags=('-a', '--all'))
    help_names: jiig.f.text('Command task name(s) or empty for top level help.',
                            repeat=None)

    def on_run(self, runtime: jiig.Runtime):
        runtime.provide_help(*self.help_names, show_hidden=self.all_tasks)
