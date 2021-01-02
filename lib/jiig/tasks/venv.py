"""Virtual environment management task."""

import os
from typing import List, Text

import jiig
from jiig.utility.console import abort, log_heading, log_message
from jiig.utility.process import run
from jiig.utility.python import build_virtual_environment, update_virtual_environment


class VenvBuildTask(jiig.Task):
    """(Re-)Build the tool virtual environment."""

    # For type inspection only.
    class Data:
        REBUILD_VENV: bool
    data: Data

    args = {
        'REBUILD_VENV!': ('-r', '--rebuild', 'Force virtual environment rebuild.'),
    }

    def on_run(self):
        if self.params.PRIMARY_TASK:
            log_heading(1, 'Build virtual environment')
        build_virtual_environment(self.params.VENV_FOLDER,
                                  packages=self.params.PIP_PACKAGES,
                                  rebuild=self.data.REBUILD_VENV,
                                  quiet=not self.params.PRIMARY_TASK)


class VenvUpdateTask(jiig.Task):
    """Update the tool virtual environment."""

    def on_run(self):
        if self.params.PRIMARY_TASK:
            log_heading(1, 'Update virtual environment')
        update_virtual_environment(self.params.VENV_FOLDER,
                                   packages=self.params.PIP_PACKAGES)


class VenvIPythonTask(jiig.Task):
    """Run ipython from virtual environment."""

    def on_run(self):
        ipython_path = self.expand_path_template('{VENV_FOLDER}/bin/ipython')
        if not os.path.exists(ipython_path):
            pip_path = self.expand_path_template('{VENV_FOLDER}/bin/pip')
            log_message('Install iPython in virtual environment.')
            run([pip_path, 'install', 'ipython'])
        try:
            env = {'PYTHONPATH': os.path.pathsep.join(self.params.LIB_FOLDERS)}
            os.execle(ipython_path, ipython_path, env)
        except Exception as exc:
            abort(f'Failed to execute "ipython" command.',
                  command_path=ipython_path,
                  exception=exc)


class VenvPipTask(jiig.Task):
    """Run pip from virtual environment."""

    # For type inspection only.
    class Data:
        ARGS: List[Text]
    data: Data

    args = {
        'ARGS[*]': 'Pip command line arguments.',
    }

    def on_run(self):
        pip_path = self.expand_path_template('{VENV_FOLDER}/bin/pip')
        os.execl(pip_path, pip_path, *self.data.ARGS)


class VenvPython(jiig.Task):
    """Run python from virtual environment."""

    # For type inspection only.
    class Data:
        ARGS: List[Text]
    data: Data

    args = {
        'ARGS[*]': 'Python command line arguments.',
    }

    def on_run(self):
        python_path = self.expand_path_template('{VENV_FOLDER}/bin/python')
        env = {'PYTHONPATH': os.path.pathsep.join(self.params.LIB_FOLDERS)}
        os.execle(python_path, python_path, *self.data.ARGS, env)


class TaskClass(jiig.Task):
    """Manage the tool virtual environment."""

    sub_tasks = {
        'build': VenvBuildTask,
        'ipython': VenvIPythonTask,
        'pip': VenvPipTask,
        'python': VenvPython,
        'update': VenvUpdateTask,
    }

    def on_run(self):
        if not self.params.VENV_ENABLED:
            abort(f'Virtual environment is disabled,',
                  f'VENV_ENABLED must be True in init.jiig.')
        if not self.params.VENV_FOLDER:
            abort(f'VENV_FOLDER is not set in init.jiig.')
