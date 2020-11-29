"""Help task."""

import jiig


@jiig.task('help',
           jiig.bool_option('ALL_TASKS',
                            ('-a', '--all'),
                            description='Show all tasks, including hidden ones'),
           jiig.argument('HELP_NAMES',
                         description='Command task name(s) or empty for top level help',
                         cardinality='*'),
           description='Display help screen',
           auxiliary_task=True)
def task_help(runner: jiig.TaskRunner):
    help_text = runner.format_help(*runner.args.HELP_NAMES,
                                   show_hidden=runner.args.ALL_TASKS)
    if help_text:
        print(help_text)
