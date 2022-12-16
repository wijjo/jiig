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
Task creation task.
"""

import os

import jiig
from jiig.util.template_expansion import expand_folder


@jiig.task(
    cli={
        'options': {
            'force': ('-f', '--force'),
        }
    },
)
def create(
    runtime: jiig.Runtime,
    force: jiig.f.boolean(),
    task_names: jiig.f.comma_list(),
    output_folder: jiig.f.filesystem_folder(absolute_path=True),
):
    """
    Create task module(s).

    :param runtime: Jiig runtime API.
    :param force: Force overwriting of target files.
    :param task_names: Comma-separated task/module names.
    :param output_folder: Generated task module output folder.
    """
    if not os.path.exists(os.path.join(output_folder, '../__init__.py')):
        runtime.abort(f'Target folder is not a Python package.', output_folder)
    expand_tasks(runtime, output_folder, task_names, force=force)


def expand_tasks(runtime: jiig.Runtime,
                 output_folder: str,
                 task_names: list[str],
                 force: bool = False,
                 quiet: bool = False,
                 ):
    """
    Expand task templates.

    :param runtime: Jiig runtime API.
    :param output_folder: Tasks output folder.
    :param task_names: Names for generated tasks.
    :param force: Overwrite existing modules if True.
    :param quiet: Suppress additional messages if True.
    """
    if not task_names:
        if not quiet:
            runtime.warning('No task names provided for expansion.')
        return
    source_folder = os.path.join(runtime.paths.jiig_root, 'templates/task')
    for task_name in task_names:
        if not quiet:
            runtime.message(f'Generating task "{task_name}".')
        expand_folder(
            source_folder,
            output_folder,
            overwrite=force,
            symbols={
                'mytask': task_name,
                'template_bool_option': f'{task_name}_bool',
                'template_string_option': f'{task_name}_string',
                'template_argument_positional': f'{task_name}_arg',
            }
        )
        if not quiet:
            runtime.message('NOTE: Make sure to link to the new task from the tool root task.')
