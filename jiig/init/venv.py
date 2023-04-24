# Copyright (C) 2021-2023, Steven Cooper
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

"""Virtual environment data initialization."""

import os
import sys
from pathlib import Path

from jiig.constants import JIIG_VENV_ROOT
from jiig.util.log import log_message
from jiig.util.python import (
    PYTHON_NATIVE_ENVIRONMENT_NAME,
    build_virtual_environment,
)


def check_virtual_environment(*,
                              tool_name: str,
                              runner_args: list[str],
                              cli_args: list[str],
                              packages: list = None,
                              ) -> Path:
    """
    Check virtual environment, build it, and restart in it as needed.

    :param tool_name: tool name
    :param runner_args: runner arguments
    :param cli_args: CLI arguments
    :param packages: optional packages to install in the virtual environment
    :return: virtual environment root Path
    """
    venv_root = JIIG_VENV_ROOT / tool_name
    interpreter_path = venv_root / 'bin' / 'python'
    if sys.executable == str(interpreter_path):
        log_message('Virtual environment is active.', debug=True)
    else:
        log_message('Activating virtual environment...', debug=True)
        build_virtual_environment(venv_root, packages=packages, quiet=True)
        if cli_args:
            # Restart inside the virtual environment with '--' inserted to help parsing.
            args = [str(interpreter_path)] + runner_args
            args.append('--')
            args.extend(cli_args)
            # Remember the original parent Python executable in an environment variable
            # in case the virtual environment needs to be rebuilt.
            os.environ[PYTHON_NATIVE_ENVIRONMENT_NAME] = sys.executable
            os.execv(args[0], args)
            # os.execv() does not return.
        else:
            sys.exit(0)
    return venv_root
