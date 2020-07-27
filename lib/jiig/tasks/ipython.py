import os
from jiig.task import map_task, TaskRunner
from jiig.utility import run, display_message, abort


@map_task('ipython', help='run ipython from virtual environment')
def task_ipython(runner: TaskRunner):
    ipython_path = runner.expand_path_template('{VENV_ROOT}/bin/ipython')
    if not os.path.exists(ipython_path):
        pip_path = runner.expand_path_template('{VENV_ROOT}/bin/pip')
        display_message('Install iPython in virtual environment.')
        run([pip_path, 'install', 'ipython'])
    try:
        os.execl(ipython_path, ipython_path)
    except Exception as exc:
        abort(f'Failed to execute "ipython" command.',
              command_path=ipython_path,
              exception=exc)
