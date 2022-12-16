# Copyright (C) 2020-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""
Python interpreter preparation, including virtual environment, if required.
"""

import os
import sys

from jiig.util.log import log_message
from jiig.util.python import build_virtual_environment, PYTHON_NATIVE_ENVIRONMENT_NAME

from jiig.internal.configuration.tool import ToolConfiguration


def prepare_interpreter(tool_config: ToolConfiguration,
                        runner_args: list[str],
                        cli_args: list[str],
                        ):
    """
    Prepare Python interpreter.

    Check for virtual environment, if required, and build as needed.

    If a virtual environment is required, but not active, restarts the program
    so that it runs in the virtual environment.

    :param tool_config: tool configuration
    :param runner_args: runner arguments
    :param cli_args: command line arguments
    """
    # Check if virtual environment needs to be activated.
    if not tool_config.venv_required:
        log_message('Virtual environment is not required.', debug=True)

    elif tool_config.venv_active:
        log_message('Virtual environment is active.', debug=True)

    else:
        # Restart in venv.
        log_message('Activating virtual environment...', debug=True)
        build_virtual_environment(tool_config.paths.venv,
                                  packages=tool_config.meta.pip_packages,
                                  rebuild=False,
                                  quiet=True)
        # Restart inside the virtual environment with '--' inserted to help parsing.
        args = [tool_config.venv_interpreter]
        if runner_args is not None:
            args.extend(runner_args)
        args.append('--')
        args.extend(cli_args)
        # Remember the original parent Python executable in an environment variable
        # in case the virtual environment needs to be rebuilt.
        os.environ[PYTHON_NATIVE_ENVIRONMENT_NAME] = sys.executable
        os.execv(args[0], args)
        # Does not return from here.

    # Initialize the Python library load path.
    for lib_folder in reversed(tool_config.paths.libraries):
        if os.path.isdir(lib_folder) and lib_folder not in sys.path:
            sys.path.insert(0, str(lib_folder))
