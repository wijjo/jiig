import os
from jiig.task import map_task, TaskRunner
from .venv import task_venv


@map_task(
    'python',
    help='run python from virtual environment',
    description='Run the Python interpreter from the virtual environment.',
    dependencies=[task_venv],
    arguments=[{'dest': 'ARGS', 'nargs': '*', 'help': 'Python command line arguments'}])
def task_python(runner: TaskRunner):
    python_path = runner.virtual_environment_program('python')
    os.execl(python_path, python_path, *runner.args.ARGS)