"""
Help task.
"""

import jiig


@jiig.task
def help_(
    runtime: jiig.Runtime,
    all_tasks: jiig.f.boolean('Show all tasks, including hidden ones.',
                              cli_flags=('-a', '--all')),
    help_names: jiig.f.text('Command task name(s) or empty for top level help.',
                            repeat=None),
):
    """Display help screen."""
    runtime.provide_help(*help_names, show_hidden=all_tasks)
