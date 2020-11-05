"""Virtual environment management task."""

import os

from jiig import task, sub_task, TaskRunner, argument
from jiig.arg import boolean, text
from jiig.internal.globals import global_data
from jiig.utility.console import abort, log_heading, log_message
from jiig.utility.process import run
from jiig.utility.python import build_virtual_environment, update_virtual_environment


@task('venv',
      description='Manage the tool virtual environment',
      hidden_task=True)
def task_venv(runner: TaskRunner):
    if not runner.params.VENV_ROOT:
        abort(f'VENV_ROOT is not set in init.jiig.')


@sub_task(task_venv, 'build',
          argument('REBUILD_VENV', boolean,
                   description='Force virtual environment rebuild',
                   flags='-r'),
          description='(Re-)Build the tool virtual environment')
def task_venv_build(runner: TaskRunner):
    if runner.params.PRIMARY_TASK:
        log_heading(1, 'Build virtual environment')
    build_virtual_environment(runner.params.VENV_ROOT,
                              packages=runner.params.PIP_PACKAGES,
                              rebuild=runner.args.REBUILD_VENV,
                              quiet=not runner.params.PRIMARY_TASK)


@sub_task(task_venv, 'update',
          description='Update the tool virtual environment')
def task_venv_build(runner: TaskRunner):
    if runner.params.PRIMARY_TASK:
        log_heading(1, 'Update virtual environment')
    update_virtual_environment(runner.params.VENV_ROOT,
                               packages=runner.params.PIP_PACKAGES)


@sub_task(task_venv, 'ipython',
          description='Run ipython from virtual environment')
def task_ipython(runner: TaskRunner):
    ipython_path = runner.expand_path_template('{VENV_ROOT}/bin/ipython')
    if not os.path.exists(ipython_path):
        pip_path = runner.expand_path_template('{VENV_ROOT}/bin/pip')
        log_message('Install iPython in virtual environment.')
        run([pip_path, 'install', 'ipython'])
    try:
        env = {'PYTHONPATH': os.path.pathsep.join(global_data.library_folders)}
        os.execle(ipython_path, ipython_path, env)
    except Exception as exc:
        abort(f'Failed to execute "ipython" command.',
              command_path=ipython_path,
              exception=exc)


@sub_task(task_venv, 'pip',
          argument('ARGS', text,
                   description='Pip command line arguments',
                   cardinality='*'),
          description='Run pip from virtual environment')
def task_pip(runner: TaskRunner):
    pip_path = runner.expand_path_template('{VENV_ROOT}/bin/pip')
    os.execl(pip_path, pip_path, *runner.args.ARGS)


@sub_task(task_venv, 'python',
          argument('ARGS', text,
                   description='Python command line arguments',
                   cardinality='*'),
          description='Run python from virtual environment')
def task_python(runner: TaskRunner):
    python_path = runner.expand_path_template('{VENV_ROOT}/bin/python')
    env = {'PYTHONPATH': os.path.pathsep.join(global_data.library_folders)}
    os.execle(python_path, python_path, *runner.args.ARGS, env)
