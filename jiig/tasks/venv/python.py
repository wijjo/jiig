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

"""Virtual environment Python  execution task."""

import os

import jiig


@jiig.task
def python(
    runtime: jiig.Runtime,
    trailing_arguments: jiig.f.text(repeat=()),
):
    """Run python from virtual environment.

    Args:
        runtime: jiig Runtime API.
        trailing_arguments: Trailing CLI arguments.
    """
    python_path = runtime.format_path('{venv_folder}/bin/python')
    os.execl(python_path, python_path, *trailing_arguments)
