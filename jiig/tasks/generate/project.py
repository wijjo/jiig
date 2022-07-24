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
Tool project creation task.
"""

import os

import jiig
from jiig.util.template_expansion import expand_folder

from .task import expand_tasks


@jiig.task(
    cli={
        'options': {
            'force': ('-f', '--force'),
            'tool_name': ('-T', '--tool-name'),
            'task_name': ('-t', '--task-name'),
        }
    }
)
def project(
    runtime: jiig.Runtime,
    force: jiig.f.boolean(),
    tool_name: jiig.f.text(),
    task_names: jiig.f.comma_list(),
    tool_folder: jiig.f.filesystem_folder(absolute_path=True) = '.',
):
    """
    Create Jiig tool project.

    :param runtime: Jiig runtime API.
    :param force: Force overwriting of target files.
    :param tool_name: Tool name (default: <folder name>).
    :param task_names: Comma-separated task names.
    :param tool_folder: Generated tool output folder.
    """
    tasks_list = ', '.join(task_names)
    trailing_comma = ',' if len(task_names) == 1 else ''
    if not tool_name:
        tool_name = os.path.basename(tool_folder)
    expand_folder(
        os.path.join(runtime.tool.jiig_root_folder, 'templates/tool/project'),
        tool_folder,
        overwrite=force,
        symbols={
            'jiig_root': runtime.tool.jiig_root_folder,
            'mytool': tool_name,
            'task_imports': tasks_list,
            'task_references': f'({tasks_list}{trailing_comma})',

        },
    )
    if task_names:
        tasks_output_folder = os.path.join(tool_folder, tool_name, 'tasks')
        expand_tasks(runtime, tasks_output_folder, task_names, quiet=True)
