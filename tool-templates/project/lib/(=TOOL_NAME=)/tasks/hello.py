import jiig
from jiig.utility import process


@jiig.task(
    'hello',
    jiig.Arg('TEXAS_STYLE',
             jiig.arg.Boolean,
             description='Greet with a drawl',
             flags='-t'),
    jiig.Arg('NAME',
             jiig.arg.String,
             description='Optional name',
             cardinality='?'),
    description='Display hello message',
)
def task_hello(runner: jiig.TaskRunner):
    greeting = 'Howdy' if runner.args.TEXAS_STYLE else 'Hello'
    if runner.args.NAME:
        greeting = f'{greeting} {runner.args.NAME}'
    process.run(['date'], quiet=True)
    print(f'''{greeting}:

Sample task module: "{__file__}"

The code in the above module demonstrates how to define a mapped task, with
options and arguments. Feel free to delete when you no longer need it.''')
