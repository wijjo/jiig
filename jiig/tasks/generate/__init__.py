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

"""Jiig tool sub-task imports."""

import os

# Avoid name conflict with task module in this package.
import jiig

from . import project, script, task


@jiig.task(tasks=(project, script, task))
def root(runtime: jiig.Runtime):
    """
    Manage tool assets.

    :param runtime: Jiig runtime API.
    """
    if os.getcwd() == runtime.paths.jiig_root:
        runtime.abort('Please run this command from an application folder.')
