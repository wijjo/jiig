"""Help task."""

import jiig


@jiig.task(
    'help',
    jiig.Arg('ALL_TASKS', jiig.arg.Boolean,
             description='Show all tasks, including hidden ones',
             flags=('-a', '--all')),
    jiig.Arg('HELP_NAMES', jiig.arg.String,
             description='Command task name(s) or empty for top level help',
             cardinality='*'),
    description='Display help screen',
    auxiliary_task=True,
)
def task_help(runner: jiig.TaskRunner):
    help_text = runner.format_help(*runner.args.HELP_NAMES,
                                   show_hidden=runner.args.ALL_TASKS)
    if help_text:
        print(help_text)
