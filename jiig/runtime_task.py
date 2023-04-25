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

"""Runtime task.

Runtime task objects are created when tasks are discovered and loaded to hold
all the information needed to access and invoke tasks.
"""

from types import ModuleType
from typing import Self, Sequence

from .constants import DEFAULT_ROOT_TASK_NAME
from .fields import TaskField
from .types import TaskFunction
from .util.log import abort
from .util.text.footnotes import NotesList, NotesDict


class RuntimeTask:
    """Runtime task information, based on a registered class.

    Also provides access to resolved fields and sub-tasks.

    Text items like description, notes, and footnotes are populated as needed
    with default values.
    """

    # noinspection PyUnresolvedReferences
    def __init__(self,
                 name: str,
                 full_name: str,
                 visibility: int,
                 description: str,
                 # For implemented task (not task group).
                 task_function: TaskFunction | None = None,
                 module: ModuleType | None = None,
                 fields: list[TaskField] | None = None,
                 # For task group.
                 sub_tasks: Sequence[Self] | None = None,
                 # Other optional fields.
                 notes: NotesList | None = None,
                 footnotes: NotesDict | None = None,
                 driver_hints: dict | None = None,
                 ):
        """Construct runtime task with resolved function/module references.

        INTERNAL: use new_...() methods to create RuntimeTask's.

        Args:
            name: task name
            full_name: fully-qualified task name
            visibility: 0=normal, 1=secondary, 2=hidden
            description: task description
            task_function: optional task implementation function (not used for
                task group)
            module: optional module (not used for task group)
            fields: optional task fields (not used for task group)
            sub_tasks: optional sub-tasks (for task group only)
            notes: optional notes
            footnotes: optional footnotes
            driver_hints: optional driver hints
        """
        self.name = name
        self.full_name = full_name
        self.visibility = visibility
        self.description = description
        self.task_function = task_function
        self.module = module
        self.fields = fields or []
        self.sub_tasks = list(sub_tasks) if sub_tasks is not None else []
        self.notes = notes or []
        self.footnotes = footnotes or {}
        self.driver_hints = driver_hints or {}

    @classmethod
    def new_task(cls,
                 *,
                 name: str,
                 full_name: str,
                 description: str,
                 task_function: TaskFunction,
                 module: ModuleType,
                 fields: list[TaskField],
                 visibility: int,
                 notes: NotesList,
                 footnotes: NotesDict,
                 hints: dict,
                 ) -> Self | None:
        """Resolve task reference to a RuntimeTask (if possible).

        Args:
            name: task name
            full_name: optional override full task name
            description: task description
            task_function: task function
            module: module containing task function
            fields: task field specifications
            visibility: visibility (0=normal, 1=secondary, 2=hidden)
            notes: notes list
            footnotes: footnotes dictionary
            hints: driver hints

        Returns:
            resolved task or None if it wasn't resolved and required is False
        """
        return RuntimeTask(
            name=name,
            full_name=full_name,
            visibility=visibility,
            description=description,
            task_function=task_function,
            module=module,
            fields=fields,
            sub_tasks=None,
            notes=notes,
            footnotes=footnotes,
            driver_hints=hints,
        )

    @classmethod
    def new_group(cls,
                  *,
                  name: str,
                  full_name: str,
                  description: str,
                  visibility: int,
                  sub_tasks: Sequence[Self],
                  notes: NotesList,
                  footnotes: NotesDict,
                  hints: dict,
                  ) -> Self | None:
        """Create RuntimeTask for task group.

        Args:
            name: task name
            full_name: optional override full task name
            description: optional override description
            visibility: visibility (0=normal, 1=secondary, 2=hidden)
            sub_tasks: sub-tasks
            notes: optional override notes as string or string list
            footnotes: optional override footnotes dictionary
            hints: optional override driver hints

        Returns:
            new RuntimeTask
        """
        return RuntimeTask(
            name=name,
            full_name=full_name,
            visibility=visibility,
            description=description,
            sub_tasks=sub_tasks,
            notes=notes,
            footnotes=footnotes,
            driver_hints=hints,
        )

    @classmethod
    def new_tree(cls,
                 *,
                 description: str,
                 sub_tasks: Sequence[Self],
                 notes: NotesList,
                 footnotes: NotesDict,
                 hints: dict,
                 ) -> Self:
        """Create RuntimeTask that is the root of a task tree.

        Args:
            sub_tasks: sub-tasks
            description: optional override description
            notes: optional override notes as string or string list
            footnotes: optional override footnotes dictionary
            hints: optional override driver hints

        Returns:
            new RuntimeTask
        """
        return RuntimeTask(
            name=DEFAULT_ROOT_TASK_NAME,
            full_name='',
            sub_tasks=sub_tasks,
            visibility=2,
            description=description,
            notes=notes,
            footnotes=footnotes,
            driver_hints=hints,
        )


def get_task_stack(root_task: RuntimeTask,
                   names: Sequence[str],
                   ) -> list[RuntimeTask]:
    """Get task stack (list) based on names list.

    Args:
        root_task: root task
        names: name stack as list

    Returns:
        sub-task stack as list
    """
    task_stack: list[RuntimeTask] = [root_task]

    def _get_sub_stack(task: RuntimeTask, sub_names: Sequence[str]):
        for sub_task in task.sub_tasks:
            if sub_task.name == sub_names[0]:
                task_stack.append(sub_task)
                if len(sub_names) > 1:
                    _get_sub_stack(sub_task, sub_names[1:])
                break
        else:
            raise ValueError(sub_names[0])

    try:
        _get_sub_stack(root_task, names)
        return task_stack
    except ValueError:
        abort(f'Failed to resolve command:', command='.'.join(names))
