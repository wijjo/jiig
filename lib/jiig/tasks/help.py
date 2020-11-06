"""Help task."""

from jiig import arg, task, argument, TaskRunner


@task('help',
      argument('ALL_TASKS', arg.boolean,
               description='Show all tasks, including hidden ones',
               flags=('-a', '--all')),
      argument('HELP_NAMES', arg.text,
               description='Command task name(s) or empty for top level help',
               cardinality='*'),
      description='Display help screen',
      auxiliary_task=True)
def task_help(runner: TaskRunner):
    help_text = runner.format_help(*runner.args.HELP_NAMES,
                                   show_hidden=runner.args.ALL_TASKS)
    if help_text:
        print(help_text)
