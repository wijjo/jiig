"""
Virtual environment and Python interpreter initialization.
"""

import os
import sys

from jiig import model
from jiig.util.console import log_message
from jiig.util.python import build_virtual_environment

from .pre_load import AppPreLoadData


def _initialize_virtual_environment(pre_load_data: AppPreLoadData,
                                    tool: model.ToolRuntime):
    # Check if a virtual environment is required and restart inside it as needed.
    # Will not return if it needs to restart in the virtual environment.

    # Do nothing if a virtual environment is not needed.
    if not tool.pip_packages and not tool.options.venv_required:
        return

    # Do nothing if already running inside the virtual environment.
    venv_interpreter = os.path.join(tool.venv_folder, 'bin', 'python')
    if sys.executable == venv_interpreter:
        return

    # Build the virtual environment as needed.
    build_virtual_environment(tool.venv_folder,
                              packages=tool.pip_packages,
                              rebuild=False,
                              quiet=True)

    # Restart inside the virtual environment with '--' inserted to help parsing.
    args = [venv_interpreter]
    if pre_load_data.runner_args is not None:
        args.extend(pre_load_data.runner_args)
    args.append('--')
    args.extend(pre_load_data.cli_args)
    log_message('Re-running inside virtual environment...', verbose=True)
    os.execl(args[0], *args)
    # Does not return from here.


def go(pre_load_data: AppPreLoadData,
       tool: model.ToolRuntime,
       ):
    """
    Initialize virtual environment if necessary.

    :param pre_load_data: pre-parsed CLI options
    :param tool: tool runtime object
    """
    # May not return.
    _initialize_virtual_environment(pre_load_data, tool)

    # Initialize the Python library loading path.
    for lib_folder in reversed(tool.library_folders):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, lib_folder)
