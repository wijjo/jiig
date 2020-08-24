"""
Jiig virtual environment management.
"""
import os

from jiig import task, TaskRunner
from jiig import utility


@task(
    'venv',
    help='manage the tool virtual environment',
)
def task_venv(runner: TaskRunner):
    if not runner.params.VENV_ROOT:
        utility.abort(f'VENV_ROOT is not set in init.jiig.')


@task(
    'build',
    parent=task_venv,
    help='(re-)build the tool virtual environment',
    options={'-r': {
        'dest': 'REBUILD_VENV',
        'action': 'store_true',
        'help': 'force virtual environment rebuild'}},
)
def task_venv_build(runner: TaskRunner):
    if runner.params.PRIMARY_TASK:
        utility.log_heading(1, 'Build virtual environment')
    utility.build_virtual_environment(runner.params.VENV_ROOT,
                                      packages=runner.params.PIP_PACKAGES,
                                      rebuild=runner.args.REBUILD_VENV,
                                      quiet=not runner.params.PRIMARY_TASK)


@task(
    'update',
    parent=task_venv,
    help='update the tool virtual environment',
)
def task_venv_build(runner: TaskRunner):
    if runner.params.PRIMARY_TASK:
        utility.log_heading(1, 'Update virtual environment')
    utility.update_virtual_environment(runner.params.VENV_ROOT,
                                       packages=runner.params.PIP_PACKAGES)


@task(
    'ipython',
    parent=task_venv,
    help='run ipython from virtual environment',
)
def task_ipython(runner: TaskRunner):
    ipython_path = runner.expand_path_template('{VENV_ROOT}/bin/ipython')
    if not os.path.exists(ipython_path):
        pip_path = runner.expand_path_template('{VENV_ROOT}/bin/pip')
        utility.log_message('Install iPython in virtual environment.')
        utility.run([pip_path, 'install', 'ipython'])
    try:
        os.execl(ipython_path, ipython_path)
    except Exception as exc:
        utility.abort(f'Failed to execute "ipython" command.',
                      command_path=ipython_path,
                      exception=exc)


@task(
    'pip',
    parent=task_venv,
    help='run pip from virtual environment',
    arguments=[{'dest': 'ARGS', 'nargs': '*', 'help': 'Pip command line arguments'}],
)
def task_pip(runner: TaskRunner):
    pip_path = runner.expand_path_template('{VENV_ROOT}/bin/pip')
    os.execl(pip_path, pip_path, *runner.args.ARGS)


@task(
    'python',
    parent=task_venv,
    help='run python from virtual environment',
    arguments=[{'dest': 'ARGS', 'nargs': '*', 'help': 'Python command line arguments'}],
)
def task_python(runner: TaskRunner):
    python_path = runner.expand_path_template('{VENV_ROOT}/bin/python')
    os.execl(python_path, python_path, *runner.args.ARGS)
