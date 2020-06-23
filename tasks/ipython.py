import os
from jiig.task import map_task, TaskRunner


@map_task(
    'ipython',
    help='run ipython from virtual environment',
    description='Run an interactive IPython session from the Python virtual environment.')
def task_ipython(runner: TaskRunner):
    ipython_path = runner.virtual_environment_program('ipython')
    if not os.path.exists(ipython_path):
        pip_path = runner.virtual_environment_program('pip')
        runner.message('Install iPython in virtual environment.')
        runner.run([pip_path, 'install', 'ipython'])
    os.execl(ipython_path, ipython_path)
