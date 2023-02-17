# Copyright (C) 2023, Steven Cooper
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
Build source distribution.
"""

import os
from pathlib import Path

import jiig


@jiig.task
def sdist(
    runtime: jiig.Runtime,
):
    """
    Build the source distribution.

    :param runtime: Jiig runtime API.
    """
    if (Path(jiig.__file__).parent.parent / 'pyproject.toml').is_file():
        runtime.heading(1, 'Build source distribution')
        python_path = runtime.format_path('{venv_folder}/bin/python')
        os.execvp(python_path, [python_path, '-m', 'build'])
    else:
        runtime.error('Not running in Jiig source environment.')
