"""
Virtual environment IPython execution task.
"""

import os

import jiig
from jiig.util.console import abort, log_message
from jiig.util.process import run


class Task(jiig.Task):
    """Run ipython from virtual environment."""

    trailing_arguments: jiig.text('Trailing CLI arguments.', cli_trailing=True)

    def on_run(self, runtime: jiig.Runtime):
        ipython_path = runtime.format_path('{venv_folder}/bin/ipython')
        if not os.path.exists(ipython_path):
            pip_path = runtime.format_path('{venv_folder}/bin/pip')
            log_message('Install iPython in virtual environment.')
            run([pip_path, 'install', 'ipython'] + self.trailing_arguments)
        try:
            env = {'PYTHONPATH': os.path.pathsep.join(runtime.tool.library_folders)}
            os.execle(ipython_path, ipython_path, env)
        except Exception as exc:
            abort(f'Failed to execute "ipython" command.',
                  command_path=ipython_path,
                  exception=exc)
