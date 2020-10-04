from jiig import task, TaskRunner


@task(
    'help',
    help='display help screen',
    options={('-a', '--all'): {
        'dest': 'ALL_TASKS',
        'action': 'store_true',
        'help': 'show all tasks, including hidden management tasks'}},
    arguments=[{'dest': 'HELP_NAMES',
                'nargs': '*',
                'help': 'command task name sequence or empty for top level help'}],
    auxiliary_task=True)
def task_help(runner: TaskRunner):
    help_text = runner.format_help(*runner.args.HELP_NAMES)
    if help_text:
        print(help_text)
