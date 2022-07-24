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
Virtual environment IPython execution task.
"""

import os

import jiig
from jiig.util.process import run


@jiig.task(
    cli={
        'trailing': 'trailing_arguments',
    },
)
def ipython(
    runtime: jiig.Runtime,
    trailing_arguments: jiig.f.text(repeat=(1, None)),
):
    """
    Run ipython from virtual environment.

    :param runtime: jiig Runtime API.
    :param trailing_arguments: Trailing CLI arguments.
    """
    ipython_path = runtime.format_path('{venv_folder}/bin/ipython')
    if not os.path.exists(ipython_path):
        pip_path = runtime.format_path('{venv_folder}/bin/pip')
        runtime.message('Install iPython in virtual environment.')
        run([pip_path, 'install', 'ipython'] + trailing_arguments)
    try:
        env = {'PYTHONPATH': os.path.pathsep.join(runtime.tool.library_folders)}
        os.execle(ipython_path, ipython_path, env)
    except Exception as exc:
        runtime.abort(f'Failed to execute "ipython" command.',
                      command_path=ipython_path,
                      exception=exc)
