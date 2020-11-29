"""
Python interpreter initialization.
"""

import os
import sys

from jiig.utility.console import log_message, abort
from jiig.utility.python import build_virtual_environment

from .parameters_initializer import ParameterData


def initialize(param_data: ParameterData):
    """
    Check if a virtual environment is required and restart inside it as needed.

    Update the Python interpreter library path.

    Will not return if it needs to restart in the virtual environment.

    :param param_data: data from preliminary command line processing
    """
    # Check if it needs to restart inside a virtual environment.
    if param_data.venv_enabled:
        # venv_root default should completely prevent, but check anyway.
        if not param_data.venv_root:
            abort('Virtual environment is enabled, but VENV_ROOT is not set.')
        venv_interpreter = os.path.join(param_data.venv_root, 'bin', 'python')
        if sys.executable != venv_interpreter:
            # Build the virtual environment as needed.
            build_virtual_environment(param_data.venv_root,
                                      packages=param_data.pip_packages,
                                      rebuild=False,
                                      quiet=True)
            # Restart inside the virtual environment with '--' inserted to help parsing.
            log_message('Re-running inside virtual environment...', verbose=True)
            os.execl(venv_interpreter,
                     venv_interpreter,
                     param_data.jiig_run_script_path,
                     param_data.tool_script_path,
                     '--',
                     *param_data.raw_arguments)

    # Add the Jiig library path if missing.
    if param_data.jiig_lib not in sys.path:
        sys.path.insert(0, param_data.jiig_lib)
    for lib_folder in reversed(param_data.library_folders):
        sys.path.insert(0, lib_folder)
    # The automatically-added Jiig root path (added due to this script) is not used, so lose it.
    if param_data.jiig_root in sys.path:
        sys.path.remove(param_data.jiig_root)
