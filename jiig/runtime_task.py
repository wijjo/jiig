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

"""Runtime task."""

from types import ModuleType
from typing import Self, Sequence

from .fields import TaskField
from .types import TaskFunction
from .util.log import abort
from .util.text.footnotes import NotesList, NotesDict


class RuntimeTask:
    """
    Runtime task information, based on a registered class.

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
        """
        Construct runtime task with resolved function/module references.

        INTERNAL: use new_...() methods to create RuntimeTask's.

        :param name: task name
        :param full_name: fully-qualified task name
        :param visibility: 0=normal, 1=secondary, 2=hidden
        :param description: task description
        :param task_function: optional task implementation function (not used for task group)
        :param module: optional module (not used for task group)
        :param fields: optional task fields (not used for task group)
        :param sub_tasks: optional sub-tasks (for task group only)
        :param notes: optional notes
        :param footnotes: optional footnotes
        :param driver_hints: optional driver hints
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
        """
        Resolve task reference to a RuntimeTask (if possible).

        :param name: task name
        :param full_name: optional override full task name
        :param description: task description
        :param task_function: task function
        :param module: module containing task function
        :param fields: task field specifications
        :param visibility: visibility (0=normal, 1=secondary, 2=hidden)
        :param notes: notes list
        :param footnotes: footnotes dictionary
        :param hints: driver hints
        :return: resolved task or None if it wasn't resolved and required is False
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
        """
        Create RuntimeTask for task group.

        :param name: task name
        :param full_name: optional override full task name
        :param description: optional override description
        :param visibility: visibility (0=normal, 1=secondary, 2=hidden)
        :param sub_tasks: sub-tasks
        :param notes: optional override notes as string or string list
        :param footnotes: optional override footnotes dictionary
        :param hints: optional override driver hints
        :return: new RuntimeTask
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
        """
        Create RuntimeTask that is the root of a task tree.

        :param sub_tasks: sub-tasks
        :param description: optional override description
        :param notes: optional override notes as string or string list
        :param footnotes: optional override footnotes dictionary
        :param hints: optional override driver hints
        :return: new RuntimeTask
        """
        return RuntimeTask(
            name='(root)',
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
    """
    Get task stack (list) based on names list.

    :param root_task: root task
    :param names: name stack as list
    :return: sub-task stack as list
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
