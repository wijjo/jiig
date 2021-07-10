"""
Help task.
"""

import jiig


@jiig.task(
    cli={
        'options': {
            'all_tasks': ('-a', '--all'),
        }
    }
)
def help_(
    runtime: jiig.Runtime,
    all_tasks: jiig.f.boolean(),
    help_names: jiig.f.text(repeat=(None, None)),
):
    """
    Display help screen.

    :param runtime: jiig Runtime API.
    :param all_tasks: Show all tasks, including hidden ones.
    :param help_names: Command task name(s) or empty for top level help.
    """
    runtime.provide_help(*help_names, show_hidden=all_tasks)
