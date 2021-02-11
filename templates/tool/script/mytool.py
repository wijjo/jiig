#!/usr/bin/env python3
"""
mytool (jiig monolithic tool script - pure-Python version).

PYTHONPATH (i.e. sys.path) must include Jiig lib for `import jiig` to work.

To use a virtual environment, either let `jiig.main()` automatically create and
restart in it or activate the virtual environment prior to running this script.
"""

import os
import jiig


HELLO_TASK = jiig.Task(
    description='Display hello message.',
    args={
        'TEXAS_STYLE[!]': ('-t', 'greet with a drawl'),
        'NAME[?]': 'optional name',
    },
)


@HELLO_TASK.run
def hello(_runner: jiig.Runner, data):
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


ROOT_TASK = jiig.Task(
    tasks={
        'hello': HELLO_TASK,
        'alias[s]': jiig.task.alias,
        'help[s]': jiig.task.help,
    },
)


TOOL = jiig.Tool(
    tool_name='mytool',
    tool_root_folder=os.path.dirname(__file__),
    description='mytool description.',
    root_task=ROOT_TASK,
)


if __name__ == '__main__':
    jiig.main(TOOL)
