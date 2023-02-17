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

import jiig.tasks
from jiig.task import (
    Task,
    TaskGroup,
    TaskTree,
)
from jiig.tool import ToolOptions
from jiig.util.log import log_error


def inject_builtin_tasks(*,
                         task_tree: TaskTree,
                         jiig_task_tree: TaskTree,
                         tool_options: ToolOptions,
                         ) -> TaskTree:
    """
    Create PreparedApplication.

    :param task_tree: tool task tree
    :param jiig_task_tree: jiig task tree
    :param tool_options: tool options
    :return: prepared application
    """
    # Access built-in tasks through by loading the Jiig Tool.
    visibility = 2 if tool_options.hide_builtin_tasks else 1
    provider = _JiigTaskTreeProvider(jiig_task_tree, visibility)
    provider.check_task('help', tool_options.disable_help)
    provider.check_group('alias', tool_options.disable_alias)
    provider.check_group('venv', False)
    if not provider.add_tasks and not provider.add_groups:
        return task_tree
    adjusted_task_tree = task_tree.copy()
    if provider.add_tasks:
        adjusted_task_tree.tasks.extend(provider.add_tasks)
    for add_group in provider.add_groups:
        # Need to override the tool package default for the added group to import.
        add_group.package = jiig.tasks
        adjusted_task_tree.groups.append(add_group)
    return adjusted_task_tree


class _JiigTaskTreeProvider:
    """
    Provide requested tasks and task groups based on Jiig configuration.

    NB: This class currently assumes the caller is only interested in top level
    tasks and task groups. It specifically assumes that requested task groups
    will not have sub-task groups.
    """

    def __init__(self, task_tree: TaskTree, visibility: int):
        self.task_tree = task_tree
        self.visibility = visibility
        self.add_tasks: list[Task] = []
        self.add_groups: list[TaskGroup] = []

    def check_task(self, name: str, disabled: bool):
        if disabled:
            return
        for task in self.task_tree.tasks:
            if task.name == name:
                task_copy = task.copy(visibility=self.visibility, impl=f'jiig.tasks.{name}')
                self.add_tasks.append(task_copy)
                break
        else:
            log_error(f'Jiig task "{name}" not found in Jiig configuration.')

    def check_group(self, name: str, disabled: bool):
        if disabled:
            return
        for group in self.task_tree.groups:
            if group.name == name:
                group_copy = group.copy(visibility=self.visibility)
                # Add implementation references to sub_tasks.
                group_copy.tasks = [
                    task.copy(impl=f'jiig.tasks.{group.name}.{task.name}')
                    for task in group_copy.tasks
                ]
                if group_copy.groups:
                    log_error(f'Ignoring "jiig.tasks.{group.name}" sub-task groups.')
                self.add_groups.append(group_copy)
                break
        else:
            log_error(f'Jiig task group "{name}" not found in Jiig configuration.')
