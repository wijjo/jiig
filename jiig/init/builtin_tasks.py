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

"""Application/tasks preparation."""

from types import ModuleType

import jiig.tasks.alias
import jiig.tasks.venv
from jiig.builtin_tasks import (
    ALIAS_TASK_GROUP,
    HELP_TASK,
    VENV_TASK_GROUP,
)
from jiig.task import (
    Task,
    TaskGroup,
    TaskTree,
)
from jiig.tool import ToolOptions
from jiig.util.log import log_error


def inject_builtin_tasks(*,
                         task_tree: TaskTree,
                         tool_options: ToolOptions,
                         ) -> TaskTree:
    """Create PreparedApplication.

    Args:
        task_tree: tool task tree
        tool_options: tool options

    Returns:
        prepared application
    """
    # Access built-in tasks through by loading the Jiig Tool.
    visibility = 2 if tool_options.hide_builtin_tasks else 1
    add_tasks: list[Task] = []
    add_groups: list[TaskGroup] = []

    def _add_task(task: Task):
        task_copy = task.copy(visibility=visibility, impl=f'jiig.tasks.{task.name}')
        add_tasks.append(task_copy)

    def _add_group(group: TaskGroup, package: ModuleType):
        group_copy = group.copy(visibility=visibility)
        # Add implementation references to sub_tasks.
        group_copy.tasks = [
            task.copy(impl=f'jiig.tasks.{group.name}.{task.name}')
            for task in group_copy.tasks
        ]
        if group_copy.groups:
            log_error(f'Ignoring "jiig.tasks.{group.name}" sub-task groups.')
        group_copy.package = package
        add_groups.append(group_copy)

    if not tool_options.disable_help:
        _add_task(HELP_TASK)
    if not tool_options.disable_alias:
        _add_group(ALIAS_TASK_GROUP, jiig.tasks.alias)
    _add_group(VENV_TASK_GROUP, jiig.tasks.venv)

    adjusted_task_tree = task_tree.copy()
    if add_tasks:
        adjusted_task_tree.tasks.extend(add_tasks)
    if add_groups:
        adjusted_task_tree.groups.extend(add_groups)
    return adjusted_task_tree
