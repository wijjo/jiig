import os
from jiig.task import map_task, TaskRunner
from tasks.venv import task_venv


@map_task(
    'pip',
    help='run pip from virtual environment',
    description='Run the Pip package manager from the virtual environment.',
    dependencies=[task_venv],
    arguments=[{'dest': 'ARGS', 'nargs': '*', 'help': 'Pip command line arguments'}])
def task_pip(runner: TaskRunner):
    pip_path = runner.virtual_environment_program('pip')
    os.execl(pip_path, pip_path, *runner.args.ARGS)
