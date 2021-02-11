"""Sample Jiig "hello world" task module."""

import jiig


TASK = jiig.Task(
    description='Display hello message.',
    args={
        'TEXAS_STYLE[!]': ('-t', 'greet with a drawl'),
        'NAME[?]': 'optional name',
    },
)


@TASK.run
def task_run(_runner: jiig.Runner, data):
    greeting = 'Howdy' if data.TEXAS_STYLE else 'Hello'
    if data.NAME:
        greeting = f'{greeting} {data.NAME}'
    jiig.util.process.run(['date'], quiet=True)
    print(f'{greeting}:')
    print('')
    print(f'Sample task script: "mytool"')
    print('')
    print('Use the sample script as a basis for defining your own custom')
    print('tool, tasks, options, and arguments.')
