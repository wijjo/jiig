# Copyright (C) 2021-2022, Steven Cooper
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

"""Jiig venv sub-task imports."""

import jiig

from . import build, ipython, pip, python, run, update


@jiig.task(tasks=(build, ipython, pip, python, run, update))
def root(runtime: jiig.Runtime):
    """
    Manage the tool virtual environment.

    :param runtime: Jiig runtime API.
    """
    if not runtime.tool.pip_packages and not runtime.tool.tool_options.venv_required:
        runtime.abort(f'A virtual environment is not required.')
    if not runtime.tool.venv_folder:
        runtime.abort(f'Virtual environment folder (venv_folder) is not set.')
