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

from jiig.constants import HOME_FOLDER_PATH, JIIG_VENV_ROOT
from jiig.util.log import log_message
from jiig.util.python import (
    PYTHON_NATIVE_ENVIRONMENT_NAME,
    build_virtual_environment,
)

from .arguments import RuntimeArguments


def check_virtual_environment(*,
                              tool_root: Path | str,
                              arguments: RuntimeArguments,
                              ) -> Path:
    """
    Check virtual environment, build it, and restart in it as needed.

    :param tool_root: tool root folder
    :param arguments: runtime arguments data
    :return: virtual environment root Path
    """
    venv_root = JIIG_VENV_ROOT / tool_root.relative_to(HOME_FOLDER_PATH)
    interpreter_path = venv_root / 'bin' / 'python'
    if sys.executable == str(interpreter_path):
        log_message('Virtual environment is active.', debug=True)
    else:
        log_message('Activating virtual environment...', debug=True)
        build_virtual_environment(venv_root, quiet=True)
        # Restart inside the virtual environment with '--' inserted to help parsing.
        args = [str(interpreter_path)]
        if arguments.runner is not None:
            args.extend(arguments.runner)
        args.append('--')
        args.extend(arguments.cli)
        # Remember the original parent Python executable in an environment variable
        # in case the virtual environment needs to be rebuilt.
        os.environ[PYTHON_NATIVE_ENVIRONMENT_NAME] = sys.executable
        os.execv(args[0], args)
        # os.execv() does not return.
    return venv_root
