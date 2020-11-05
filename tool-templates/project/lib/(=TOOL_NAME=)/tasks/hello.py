from jiig import task, argument, TaskRunner
from jiig.arg import boolean, text
from jiig.utility import process


@task('hello',
      argument('TEXAS_STYLE',
               boolean,
               description='Greet with a drawl',
               flags='-t'),
      argument('NAME',
               text,
               description='Optional name',
               cardinality='?'),
      description='Display hello message', )
def task_hello(runner: TaskRunner):
    greeting = 'Howdy' if runner.args.TEXAS_STYLE else 'Hello'
    if runner.args.NAME:
        greeting = f'{greeting} {runner.args.NAME}'
    process.run(['date'], quiet=True)
    print(f'''{greeting}:

Sample task module: "{__file__}"

The code in the above module demonstrates how to define a mapped task, with
options and arguments. Feel free to delete when you no longer need it.''')
