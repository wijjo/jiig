"""
Virtual environment IPython execution task.
"""

import os

import jiig
from jiig.util.process import run


@jiig.task
def ipython(
    runtime: jiig.Runtime,
    trailing_arguments: jiig.f.text('Trailing CLI arguments.', cli_trailing=True),
):
    """Run ipython from virtual environment."""
    ipython_path = runtime.format_path('{venv_folder}/bin/ipython')
    if not os.path.exists(ipython_path):
        pip_path = runtime.format_path('{venv_folder}/bin/pip')
        runtime.message('Install iPython in virtual environment.')
        run([pip_path, 'install', 'ipython'] + trailing_arguments)
    try:
        env = {'PYTHONPATH': os.path.pathsep.join(runtime.tool.library_folders)}
        os.execle(ipython_path, ipython_path, env)
    except Exception as exc:
        runtime.abort(f'Failed to execute "ipython" command.',
                      command_path=ipython_path,
                      exception=exc)
