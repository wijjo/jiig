"""Sample Jiig "hello world" task module."""

import jiig
from jiig.utility import process


@jiig.task(
    'hello',
    jiig.option('TEXAS_STYLE', '-t', description='greet with a drawl'),
    jiig.argument('NAME', cardinality='?', description='optional name'),
    description='Display hello message',
)
def task_hello(runner: jiig.TaskRunner):
    greeting = 'Howdy' if runner.args.TEXAS_STYLE else 'Hello'
    if runner.args.NAME:
        greeting = f'{greeting} {runner.args.NAME}'
    process.run(['date'], quiet=True)
    print(f'{greeting}:')
    print('')
    print(f'Sample task module: "{__file__}"')
    print('')
    print('Use the sample code as a basis for defining your own custom')
    print('tool, tasks, options, and arguments.')
