from jiig.task import map_task, TaskRunner


@map_task(
    'help',
    help='display help screen',
    arguments=[{'dest': 'HELP_NAMES',
                'nargs': '*',
                'help': 'command task name sequence or empty for top level help'}])
def task_help(runner: TaskRunner):
    help_text = runner.format_help(*runner.args.HELP_NAMES)
    if help_text:
        print(help_text)
