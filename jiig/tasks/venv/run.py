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

"""Virtual environment general command execution task."""

import os

import jiig


@jiig.task
def run(
    runtime: jiig.Runtime,
    command: jiig.f.text(),
    trailing_arguments: jiig.f.text(repeat=()),
):
    """Run miscellaneous command from virtual environment.

    Args:
        runtime: jiig Runtime API.
        command: Virtual environment command.
        trailing_arguments: Trailing CLI arguments.
    """
    command_path = runtime.format_path(f'{{venv_folder}}/bin/{command}')
    if not os.path.isfile(command_path):
        runtime.abort(f'Command "{command}" does not exist in virtual environment.')
    os.execl(command_path, command_path, *trailing_arguments)
