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
Help task.
"""

import jiig


@jiig.task(
    cli={
        'options': {
            'all_tasks': ('-a', '--all'),

        }
    },
)
def help_(
    runtime: jiig.Runtime,
    all_tasks: jiig.f.boolean(),
    help_names: jiig.f.text(repeat=(None, None)),
):
    """
    Display tool help or task help (if task name(s) are provided).

    :param runtime: jiig Runtime API.
    :param all_tasks: Show all tasks, including hidden ones.
    :param help_names: Command task name(s) or empty for top level help.
    """
    runtime.provide_help(*help_names, show_hidden=all_tasks)
