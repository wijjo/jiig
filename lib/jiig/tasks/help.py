"""Help task."""

from jiig import task, TaskRunner


@task(
    'help',
    help='display help screen',
    arguments=[
        (['-a', '--all'],
         {'dest': 'ALL_TASKS',
          'action': 'store_true',
          'help': 'show all tasks, including hidden ones'}),
        {'dest': 'HELP_NAMES',
         'nargs': '*',
         'help': 'command task name sequence or empty for top level help'}
    ],
    auxiliary_task=True)
def task_help(runner: TaskRunner):
    help_text = runner.format_help(*runner.args.HELP_NAMES,
                                   show_hidden=runner.args.ALL_TASKS)
    if help_text:
        print(help_text)
