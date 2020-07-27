import os
from jiig.task import map_task, TaskRunner


@map_task(
    'pip',
    help='run pip from virtual environment',
    arguments=[{'dest': 'ARGS', 'nargs': '*', 'help': 'Pip command line arguments'}],
)
def task_pip(runner: TaskRunner):
    pip_path = runner.expand_path_template('{VENV_ROOT}/bin/pip')
    os.execl(pip_path, pip_path, *runner.args.ARGS)
