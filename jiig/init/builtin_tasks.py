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

from jiig.runtime import RuntimePaths
from jiig.task import TaskTree
from jiig.tool import ToolOptions


def inject_builtin_tasks(*,
                         tool_task_tree: TaskTree,
                         jiig_task_tree: TaskTree,
                         tool_options: ToolOptions,
                         paths: RuntimePaths,
                         ) -> TaskTree:
    """
    Create PreparedApplication.

    :param tool_task_tree: tool task tree
    :param jiig_task_tree: jiig task tree
    :param tool_options: tool options
    :param paths: runtime paths
    :return: prepared application
    """
    # Do nothing for the Jiig tool itself.
    if paths.tool_root == paths.jiig_root:
        return tool_task_tree
    # Access built-in tasks through by loading the Jiig Tool.
    injector = _BuiltinTaskInjector(
        tool_task_tree,
        jiig_task_tree,
        2 if tool_options.hide_builtin_tasks else 1,
    )
    # Inject built-in tasks as needed.
    injector.inject_task('help', tool_options.disable_help)
    injector.inject_group('alias', tool_options.disable_alias)
    injector.inject_group('venv', not tool_options.venv_required)
    # Provide adjusted task tree with built-in tasks present.
    return injector.adjusted_task_tree


class _BuiltinTaskInjector:

    def __init__(self,
                 tool_task_tree: TaskTree,
                 jiig_task_tree: TaskTree,
                 visibility: int):
        self.jiig_task_tree = jiig_task_tree
        self.visibility = visibility
        self.adjusted_task_tree = tool_task_tree.copy()

    def inject_task(self, name: str, disable: bool):
        if self._skip(name, disable):
            return
        for built_in_task in self.jiig_task_tree.tasks:
            if built_in_task.name == name:
                adjusted_task = built_in_task.copy(visibility=self.visibility)
                adjusted_task.impl = f'jiig.tasks.{name}'
                self.adjusted_task_tree.tasks.append(adjusted_task)

    def inject_group(self, name: str, disable: bool):
        if self._skip(name, disable):
            return
        for built_in_group in self.jiig_task_tree.groups:
            if built_in_group.name == name:
                adjusted_group = built_in_group.copy(visibility=self.visibility)
                adjusted_group.package = f'jiig.tasks.{name}'
                self.adjusted_task_tree.groups.append(adjusted_group)

    def _skip(self, name: str, disable: bool) -> bool:
        return disable or name in self.adjusted_task_tree.names
