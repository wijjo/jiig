# Copyright (C) 2020-2023, Steven Cooper
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
Jiig task decorator and discovery.
"""
import os
import sys
import textwrap
from dataclasses import dataclass
from inspect import isfunction, ismodule
from types import ModuleType
from typing import Sequence, Self, TypeVar, Type, Any

from .types import TaskFunction, TaskReference, ModuleReference
from .util.collections import make_list
from .util.log import log_error, log_message, log_heading
from .util.text.footnotes import NotesSpec, NotesList, NotesDict

T_task_or_group = TypeVar('T_task_or_group')


class _BaseTask:

    dump_indent = '   '

    @classmethod
    def format_dump(cls,
                    name: str,
                    indent: str | None,
                    **members,
                    ) -> str:
        heading = f'{cls.__name__}["{name}"]:'
        member_strings = [
            f'{member_name}={member_value}'
            for member_name, member_value in members.items()
        ]
        member_text = textwrap.indent(os.linesep.join(member_strings), cls.dump_indent)
        return textwrap.indent(os.linesep.join([heading, member_text]), indent or '')

    @staticmethod
    def format_dump_string(value: str | None) -> str:
        if value is None:
            return 'None'
        return f'"{value}"'

    @staticmethod
    def format_dump_notes(value: NotesList | NotesDict | None) -> str:
        if value is None:
            return 'None'
        return f'"{textwrap.shorten(str(value)[1:-1], 40)}"'


class Task(_BaseTask):
    """
    Task specification.

    For clarity, requires only keyword arguments.
    """
    def __init__(self,
                 *,
                 name: str,
                 impl: TaskReference | None = None,
                 visibility: int = 0,
                 description: str | None = None,
                 notes: NotesSpec | None = None,
                 footnotes: NotesDict | None = None,
                 **hints,
                 ):
        """
        Task constructor.

        :param name: task name
        :param impl: optional Task implementation reference (default: the name
                     is a module in the containing TaskGroup package)
        :param visibility: 0=normal, 1=secondary, 2=hidden
        :param description: optional description
        :param notes: optional notes as string or string list
        :param footnotes: optional footnotes dictionary
        :param hints: optional driver hints (avoid collisions with other keywords)
        """
        self.name = name
        self.visibility = visibility
        self.impl: TaskReference | None = impl
        self.description: str | None = description
        self.notes: NotesList | None = make_list(notes, allow_none=True)
        self.footnotes: NotesDict | None = footnotes
        self.hints: dict = hints

    def copy(self, visibility: int = None, impl: TaskReference | None = None) -> Self:
        """
        Copy this task.

        :param visibility: optional override visibility
        :param impl: optional override implementation reference
        :return: task copy
        """
        task_copy = Task(
            name=self.name,
            impl=impl if impl is not None else self.impl,
            visibility=visibility if visibility is not None else self.visibility,
            description=self.description,
            notes=self.notes.copy() if self.notes is not None else None,
            footnotes=self.footnotes.copy() if self.footnotes is not None else None,
            **self.hints,
        )
        return task_copy

    @classmethod
    def from_raw_data(cls, name: str, raw_data: Any) -> Self:
        """
        Task creation based in raw input data (should be dictionary).

        :param name: task name
        :param raw_data: raw input data
        :return: Task object
        """
        converter = _TaskTreeElementConverter(raw_data)
        return cls(
             name=name,
             impl=converter.get_impl(),
             visibility=converter.get_visibility(),
             description=converter.get_description(),
             notes=converter.get_notes(),
             footnotes=converter.get_footnotes(),
             **converter.get_hints(),
         )

    def dump(self, indent: str = None) -> str:
        """
        Format data as text block for logging.

        :param indent: indent string if nested
        :return: formatted text block
        """
        return self.format_dump(
            self.name,
            indent,
            visibility=self.visibility,
            impl=self.impl,
            description=self.format_dump_string(self.description),
            notes=self.format_dump_notes(self.notes),
            footnotes=self.format_dump_notes(self.footnotes),
        )


class TaskGroup(_BaseTask):
    """
    Group of tasks and or nested task groups.

    For clarity, requires only keyword arguments.
    """
    def __init__(self,
                 *,
                 name: str,
                 sub_tasks: Sequence[Task | Self],
                 package: ModuleReference | None = None,
                 description: str = None,
                 visibility: int = 0,
                 notes: NotesSpec | None = None,
                 footnotes: NotesDict | None = None,
                 **hints,
                 ):
        """
        TaskGroup constructor.

        Task group description is required because there is nowhere else to get
        it. There is no associated function or object with a doc string.

        :param name: task group name
        :param sub_tasks: nested sub-tasks and or sub-groups
        :param package: optional package containing task modules - allows simple
                        name task implementation references
        :param description: optional description (default: task package description)
        :param visibility: 0=normal, 1=secondary, 2=hidden
        :param notes: optional notes as string or string list
        :param footnotes: optional footnotes dictionary
        :param hints: optional driver hints (avoid collisions with other keywords)
        """
        self.name = name
        self.visibility = visibility
        self.package = package
        self.description = description
        sub_task_scrubber = _TaskGroupSubTaskScrubber()
        self.groups: list[TaskGroup] = sub_task_scrubber.scrub_sub_tasks(
            self.name, sub_tasks, TaskGroup)
        self.tasks: list[Task] = sub_task_scrubber.scrub_sub_tasks(
            self.name, sub_tasks, Task)
        self.notes: NotesList | None = make_list(notes, allow_none=True)
        self.footnotes: NotesDict | None = footnotes
        self.hints: dict = hints

    def copy(self, visibility: int = None) -> Self:
        """
        Copy this task group.

        :param visibility: optional visibility override
        :return: task group copy
        """
        group_copy = TaskGroup(
            name=self.name,
            sub_tasks=[],
            package=self.package,
            description=self.description,
            visibility=visibility if visibility is not None else self.visibility,
            notes=self.notes.copy() if self.notes is not None else None,
            footnotes=self.footnotes.copy() if self.footnotes is not None else None,
            **self.hints,
        )
        group_copy.tasks = self.tasks.copy()
        group_copy.groups = self.groups.copy()
        return group_copy

    @classmethod
    def from_raw_data(cls, name: str, raw_data: Any) -> Self:
        """
        TaskGroup creation based in raw input data (should be dictionary).

        Recursively creates contained TaskGroup and Task objects.

        :param name: task group name
        :param raw_data: raw input data
        :return: TaskGroup object
        """
        converter = _TaskTreeElementConverter(raw_data)
        return cls(
            name=name,
            sub_tasks=converter.get_sub_tasks(),
            package=converter.get_package(),
            description=converter.get_description(),
            visibility=converter.get_visibility(),
            notes=converter.get_notes(),
            footnotes=converter.get_footnotes(),
            **converter.get_hints(),
        )

    def dump(self, indent: str = None) -> str:
        """
        Format data as text block for logging.

        :param indent: indent string if nested
        :return: formatted text block
        """
        if indent is None:
            indent = ''
        group_dump = self.format_dump(
            self.name,
            indent,
            package=self.format_dump_string(self.package),
            description=self.format_dump_string(self.description),
            visibility=self.visibility,
            notes=self.format_dump_notes(self.notes),
            footnotes=self.format_dump_notes(self.footnotes),
        )
        sub_task_dumps: list[str] = [
            sub_task.dump(indent + self.dump_indent)
            for sub_task in self.tasks
        ]
        sub_group_dumps: list[str] = [
            sub_group.dump(indent + self.dump_indent)
            for sub_group in self.groups
        ]
        return (os.linesep * 2).join([group_dump] + sub_task_dumps + sub_group_dumps)


class TaskTree(TaskGroup):
    """
    Application task tree.

    For clarity, requires only keyword arguments.
    """
    def __init__(self,
                 *,
                 name: str,
                 sub_tasks: Sequence[Task | TaskGroup],
                 package: ModuleReference | None = None,
                 ):
        """
        TaskGroup constructor.

        :param name: task tree name
        :param sub_tasks: nested sub-tasks and or sub-groups
        :param package: optional package containing top level task modules -
                        allows simple name task implementation references
        """
        super().__init__(name=name,
                         sub_tasks=sub_tasks,
                         package=package,
                         description='root task',
                         visibility=2)

    def copy(self, visibility: int = None) -> Self:
        """
        Copy this task group.

        :param visibility: optional visibility override
        :return: task group copy
        """
        tree_copy = TaskTree(
            name=self.name,
            sub_tasks=[],
            package=self.package,
        )
        tree_copy.tasks = self.tasks.copy()
        tree_copy.groups = self.groups.copy()
        return tree_copy

    @classmethod
    def from_raw_data(cls, name: str, raw_data: Any) -> Self:
        """
        TaskTree creation based in raw input data (should be dictionary).

        Recursively creates contained TaskGroup and Task objects.

        :param name: task tree name
        :param raw_data: raw input data
        :return: TaskTree object
        """
        converter = _TaskTreeElementConverter(raw_data)
        task_tree = cls(
            name=name,
            sub_tasks=converter.get_sub_tasks(),
            package=converter.get_package(),
        )
        hints = converter.get_hints()
        if hints:
            log_error('Ignoring unexpected task tree hint keys:', *sorted(hints.keys()))
        return task_tree

    def log_dump_all(self, heading: str = None):
        """
        Dump task tree to log, e.g. console.

        :param heading: optional heading text
        """
        log_heading(heading or 'task tree', is_error=True)
        log_message(self.dump(), is_error=True)
        log_heading('', is_error=True)


@dataclass
class RegisteredTask:
    """Registered task specification."""
    task_function: TaskFunction
    module: ModuleType
    full_name: str
    description: str | None
    notes: NotesSpec | None
    footnotes: NotesDict | None


TASKS_BY_FUNCTION_ID: dict[int, RegisteredTask] = {}
TASKS_BY_MODULE_ID: dict[int, RegisteredTask] = {}


def task(
    naked_task_function: TaskFunction = None,
    /,
    description: str = None,
    notes: NotesSpec = None,
    footnotes: NotesDict = None,
) -> TaskFunction:
    """
    Task function decorator.

    :param naked_task_function: not used explicitly, only non-None for naked @task functions
    :param description: task description (default: parsed from doc string)
    :param notes: optional note or notes text
    :param footnotes: optional footnotes dictionary
    :return: wrapper task function
    """
    if naked_task_function is None:
        # The decorator was called with parenthesized arguments.
        def _task_function_wrapper(task_function: TaskFunction) -> TaskFunction:
            _register_task_function(
                task_function=task_function,
                task_description=description,
                task_notes=notes,
                task_footnotes=footnotes,
            )
            return task_function

        return _task_function_wrapper

    # The decorator was invoked "naked", without parentheses or arguments.
    _register_task_function(naked_task_function)
    return naked_task_function


def _register_task_function(
        task_function: TaskFunction,
        task_description: str | None = None,
        task_notes: NotesSpec = None,
        task_footnotes: NotesDict = None,
):
    # task_function.__module__ may be None, e.g. for tasks in a Jiig script.
    module_name = getattr(task_function, '__module__')
    if module_name == 'builtins':
        module_name = '<tool>'
    module = sys.modules.get(module_name)
    registered_task = RegisteredTask(
        task_function=task_function,
        module=module,
        full_name=f'{module_name}.{task_function.__name__}()',
        description=task_description,
        notes=task_notes,
        footnotes=task_footnotes,
    )
    TASKS_BY_FUNCTION_ID[id(task_function)] = registered_task
    if module is not None:
        TASKS_BY_MODULE_ID[id(registered_task.module)] = registered_task


class _TaskGroupSubTaskScrubber:

    def __init__(self):
        self.names: set[str] = set()

    def scrub_sub_tasks(self,
                        parent_name: str,
                        sub_tasks: Sequence[Task | TaskGroup],
                        filter_type: Type[T_task_or_group],
                        ) -> list[T_task_or_group]:
        scrubbed: list[T_task_or_group] = []
        for sub_task in sub_tasks:
            if isinstance(sub_task, filter_type):
                if sub_task.name not in self.names:
                    self.names.add(sub_task.name)
                    scrubbed.append(sub_task)
                else:
                    log_error(f'Ignoring repeated sub-task name in task group'
                              f' "{parent_name}": {sub_task.name}')
        return scrubbed


class _TaskTreeElementConverter:
    unnamed_count = 0

    def __init__(self, raw_data: Any):
        self.keys_used: list[str] = []
        if isinstance(raw_data, dict):
            self.raw_data = raw_data
        elif raw_data is None:
            self.raw_data = {}
        else:
            log_error('Task tree element data is not a dictionary.')
            self.raw_data = {}

    def _get_raw_data(self, name: str) -> Any | None:
        if name not in self.keys_used:
            self.keys_used.append(name)
        return self.raw_data.get(name)

    def get_name(self) -> str:
        """
        Convert raw data to name, with handling of unnamed elements.

        :return: name
        """
        raw_data = self._get_raw_data('name')
        if not raw_data:
            self.unnamed_count += 1
            return f'unnamed_{self.unnamed_count}'
        return str(raw_data)

    def get_description(self) -> str | None:
        """
        Convert raw data to description.

        :return: description or None
        """
        raw_data = self._get_raw_data('description')
        if raw_data is None:
            return None
        if not isinstance(raw_data, str):
            return str(raw_data)
        return raw_data

    def get_visibility(self) -> int:
        """
        Convert raw data to visibility.

        :return: visibility
        """
        raw_data = self._get_raw_data('visibility')
        if raw_data is None:
            return 0
        if not isinstance(raw_data, int) or raw_data < 0 or raw_data > 2:
            log_error(f'Bad visibility value: {raw_data}')
            return 0
        return raw_data

    def get_notes(self) -> NotesList | None:
        """
        Convert raw data to notes.

        :return: notes list or None
        """
        raw_data = self._get_raw_data('notes')
        if raw_data is None:
            return None
        if isinstance(raw_data, list):
            return raw_data
        if isinstance(raw_data, str):
            return [raw_data]
        if isinstance(raw_data, tuple):
            return list(raw_data)
        return [str(raw_data)]

    def get_footnotes(self) -> NotesDict | None:
        """
        Convert raw data to footnotes.

        :return: footnotes dictionary or None
        """
        raw_data = self._get_raw_data('footnotes')
        if raw_data is None:
            return None
        if isinstance(raw_data, dict):
            return {
                name: str(value)
                for name, value in raw_data.items()
            }
        log_error('Bad footnotes data:', raw_data)
        return None

    def get_hints(self) -> dict:
        """
        Extract hints from raw data based on unused dictionary keys.

        :return: hints dictionary
        """
        return {
            name: value
            for name, value in self.raw_data.items()
            if name not in self.keys_used
        }

    def get_sub_tasks(self) -> list[Task | TaskGroup]:
        """
        Convert raw data to sub_tasks list.

        :return: sub-tasks list
        """
        raw_data = self._get_raw_data('sub_tasks')
        if raw_data is None:
            return []
        if not isinstance(raw_data, dict):
            log_error('Sub-tasks raw data is not a dictionary.')
            return []
        sub_tasks: list[Task | TaskGroup] = []
        for name, raw_item_data in raw_data.items():
            if isinstance(raw_item_data, dict) and 'sub_tasks' in raw_item_data:
                sub_tasks.append(TaskGroup.from_raw_data(name, raw_item_data))
            else:
                sub_tasks.append(Task.from_raw_data(name, raw_item_data))
        return sub_tasks

    def get_package(self) -> ModuleReference | None:
        """
        Convert raw data to package module reference.

        :return: package module reference or None
        """
        raw_data = self._get_raw_data('package')
        if raw_data is None:
            return None
        if not isinstance(raw_data, str) and not ismodule(raw_data):
            log_error(f'Bad package module reference: {raw_data}')
            return None
        return raw_data

    def get_impl(self) -> TaskReference | None:
        """
        Convert raw data to task reference.

        :return: task reference or None
        """
        raw_data = self._get_raw_data('impl')
        if raw_data is None:
            return None
        if not isinstance(raw_data, str) and not ismodule(raw_data) and not isfunction(raw_data):
            log_error(f'Bad task implementation reference: {raw_data}')
            return None
        return raw_data
