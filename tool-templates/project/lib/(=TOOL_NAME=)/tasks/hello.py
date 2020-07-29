import jiig


@jiig.task(
    'hello',
    help='display hello message',
    # See ArgumentParser.add_argument() keyword arguments.
    options={
        '-t': {'dest': 'TEXAS_STYLE', 'action': 'store_true', 'help': 'greet with a drawl'},
    },
    arguments=[
        {'dest': 'NAME', 'nargs': '?', 'help': 'optional name'}
    ],
)
def task_hello(runner: jiig.TaskRunner):
    greeting = 'Howdy' if runner.args.TEXAS_STYLE else 'Hello'
    if runner.args.NAME:
        greeting = f'{greeting} {runner.args.NAME}'
    jiig.utility.run(['date'], quiet=True)
    print(f'''{greeting}:

Sample task module: "{__file__}"

The code in the above module demonstrates how to define a mapped task, with
options and arguments. Feel free to delete when you no longer need it.''')
