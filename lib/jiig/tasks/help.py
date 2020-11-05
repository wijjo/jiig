"""Help task."""

from jiig import task, argument, TaskRunner
from jiig.arg import boolean, text


@task('help',
      argument('ALL_TASKS', boolean,
               description='Show all tasks, including hidden ones',
               flags=('-a', '--all')),
      argument('HELP_NAMES', text,
               description='Command task name(s) or empty for top level help',
               cardinality='*'),
      description='Display help screen',
      auxiliary_task=True)
def task_help(runner: TaskRunner):
    help_text = runner.format_help(*runner.args.HELP_NAMES,
                                   show_hidden=runner.args.ALL_TASKS)
    if help_text:
        print(help_text)
