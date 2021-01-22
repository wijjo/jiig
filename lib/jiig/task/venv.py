"""Virtual environment management task."""

import os
from typing import List, Text

from jiig import model
from jiig.util.console import abort, log_heading, log_message
from jiig.util.process import run
from jiig.util.python import build_virtual_environment, update_virtual_environment


class VenvBuildTask(model.Task):
    """(Re-)Build the tool virtual environment."""

    # For type inspection only.
    class Data:
        REBUILD_VENV: bool
    data: Data

    args = {
        'REBUILD_VENV!': ('-r', '--rebuild', 'Force virtual environment rebuild.'),
    }

    def on_run(self):
        if not self.is_secondary:
            log_heading(1, 'Build virtual environment')
        build_virtual_environment(self.configuration.venv_folder,
                                  packages=self.configuration.pip_packages,
                                  rebuild=self.data.REBUILD_VENV,
                                  quiet=self.is_secondary)


class VenvUpdateTask(model.Task):
    """Delete the tool virtual environment."""

    def on_run(self):
        if not self.is_secondary:
            log_heading(1, 'Delete virtual environment')
        update_virtual_environment(self.configuration.venv_folder,
                                   packages=self.configuration.pip_packages)


class VenvIPythonTask(model.Task):
    """Run ipython from virtual environment."""

    options = model.TaskOptions(receive_trailing_arguments=True)

    def on_run(self):
        ipython_path = self.expand_path_template('{VENV_FOLDER}/bin/ipython')
        if not os.path.exists(ipython_path):
            pip_path = self.expand_path_template('{VENV_FOLDER}/bin/pip')
            log_message('Install iPython in virtual environment.')
            run([pip_path, 'install', 'ipython'] + self.trailing_arguments)
        try:
            env = {'PYTHONPATH': os.path.pathsep.join(self.configuration.library_folders)}
            os.execle(ipython_path, ipython_path, env)
        except Exception as exc:
            abort(f'Failed to execute "ipython" command.',
                  command_path=ipython_path,
                  exception=exc)


class VenvPipTask(model.Task):
    """Run pip from virtual environment."""

    options = model.TaskOptions(receive_trailing_arguments=True)

    def on_run(self):
        pip_path = self.expand_path_template('{VENV_FOLDER}/bin/pip')
        os.execl(pip_path, pip_path, *self.trailing_arguments)


class VenvPython(model.Task):
    """Run python from virtual environment."""

    # For type inspection only.
    class Data:
        ARGS: List[Text]
    data: Data

    options = model.TaskOptions(receive_trailing_arguments=True)

    def on_run(self):
        python_path = self.expand_path_template('{VENV_FOLDER}/bin/python')
        env = {'PYTHONPATH': os.path.pathsep.join(self.configuration.library_folders)}
        os.execle(python_path, python_path, *self.trailing_arguments, env)


class VenvRunTask(model.Task):
    """Run miscellaneous command from virtual environment."""

    # For type inspection only.
    class Data:
        COMMAND: Text
        ARGS: List[Text]
    data: Data

    options = model.TaskOptions(receive_trailing_arguments=True)

    args = {
        'COMMAND': 'Virtual environment command',
    }

    def on_run(self):
        command_path = self.expand_path_template(f'{{VENV_FOLDER}}/bin/{self.data.COMMAND}')
        if not os.path.isfile(command_path):
            abort(f'Command "{self.data.COMMAND}" does not exist in virtual environment.')
        os.execl(command_path, command_path, *self.trailing_arguments)


class TaskClass(model.Task):
    """Manage the tool virtual environment."""

    sub_tasks = {
        'build': VenvBuildTask,
        'ipython': VenvIPythonTask,
        'pip': VenvPipTask,
        'python': VenvPython,
        'run': VenvRunTask,
        'update': VenvUpdateTask,
    }

    def on_run(self):
        if not self.configuration.pip_packages and not self.configuration.venv_required:
            abort(f'A virtual environment is not required.')
        if not self.configuration.venv_folder:
            abort(f'Virtual environment folder (venv_folder) is not set.')
