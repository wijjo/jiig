"""
Virtual environment IPython execution task.
"""

import os

import jiig
from jiig.util.console import abort, log_message
from jiig.util.process import run


TASK = jiig.Task(
    description='Run ipython from virtual environment.',
    receive_trailing_arguments=True,
)


@TASK.run
def task_run(runner: jiig.Runner, _data):
    ipython_path = runner.expand_path_template('{VENV_FOLDER}/bin/ipython')
    if not os.path.exists(ipython_path):
        pip_path = runner.expand_path_template('{VENV_FOLDER}/bin/pip')
        log_message('Install iPython in virtual environment.')
        run([pip_path, 'install', 'ipython'] + runner.trailing_arguments)
    try:
        env = {'PYTHONPATH': os.path.pathsep.join(runner.tool.library_folders)}
        os.execle(ipython_path, ipython_path, env)
    except Exception as exc:
        abort(f'Failed to execute "ipython" command.',
              command_path=ipython_path,
              exception=exc)
