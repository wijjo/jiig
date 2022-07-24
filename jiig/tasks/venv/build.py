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

"""
Virtual environment build sub-task.
"""

import jiig
from jiig.util.python import build_virtual_environment


@jiig.task(
    cli={
        'options': {
            'rebuild_venv': ('-r', '--rebuild'),
        }
    }
)
def build(
    runtime: jiig.Runtime,
    rebuild_venv: jiig.f.boolean(),
):
    """
    (Re-)Build the tool virtual environment.

    :param runtime: Jiig runtime API.
    :param rebuild_venv: Force virtual environment rebuild.
    """
    runtime.heading(1, 'Build virtual environment')
    build_virtual_environment(runtime.tool.venv_folder,
                              packages=runtime.tool.pip_packages,
                              rebuild=rebuild_venv,
                              quiet=False)
