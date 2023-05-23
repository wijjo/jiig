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

"""Jiig task decorator and classes for task discovery."""

import os
import re
import sys
import textwrap
from dataclasses import dataclass
from inspect import (
    isfunction,
    ismodule,
)
from types import ModuleType
from typing import (
    Any,
    Self,
    Sequence,
    TypeVar,
)

from .constants import (
    BUILTIN_TASK_NAME_FORMAT,
    BUILTIN_TASK_NAME_PATTERN,
    DEFAULT_ROOT_TASK_NAME,
)
from .types import (
    TaskField,
    TaskFunction,
    TaskReference,
)
from .util.collections import make_list
from .util.log import (
    abort,
    log_error,
    log_message,
    log_heading,
)
from .util.text.footnotes import (
    NotesSpec,
    NotesList,
    NotesDict,
)

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
    """Task specification.

    For clarity, requires keyword arguments.
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
        """Task constructor.

        Args:
            name: task name
            impl: optional Task implementation reference (default: the name is a
                module in the containing TaskGroup package)
            visibility: 0=normal, 1=secondary, 2=hidden
            description: optional description
            notes: optional notes as string or string list
            footnotes: optional footnotes dictionary
            **hints: optional driver hints (avoid collisions with other
                keywords)
        """
        self.name = name
        self.visibility = visibility
        self.impl: TaskReference | None = impl
        self.description: str | None = description
        self.notes: NotesList | None = make_list(notes, allow_none=True)
        self.footnotes: NotesDict | None = footnotes
        self.hints: dict = hints

    def copy(self, visibility: int = None, impl: TaskReference | None = None) -> Self:
        """Copy this task.

        Args:
            visibility: optional override visibility
            impl: optional override implementation reference

        Returns:
            task copy
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
        """Task creation based in raw input data (should be dictionary).

        Args:
            name: task name
            raw_data: raw input data

        Returns:
            Task object
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
        """Format data as text block for logging.

        Args:
            indent: indent string if nested

        Returns:
            formatted text block
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
    """Group of tasks and or nested task groups.

    For clarity, requires keyword arguments.
    """
    def __init__(self,
                 *,
                 name: str,
                 sub_tasks: Sequence[Task | Self],
                 description: str = None,
                 visibility: int = 0,
                 notes: NotesSpec | None = None,
                 footnotes: NotesDict | None = None,
                 **hints,
                 ):
        """TaskGroup constructor.

        Task group description is required because there is nowhere else to get
        it. There is no associated function or object with a doc string.

        Args:
            name: task group name, or built-in task as '@name"
            sub_tasks: nested sub-tasks and or sub-groups
            description: optional description (default: task package
                description)
            visibility: 0=normal, 1=secondary, 2=hidden
            notes: optional notes as string or string list
            footnotes: optional footnotes dictionary
            **hints: optional driver hints (avoid collisions with other
                keywords)
        """
        self.name = name
        self.visibility = visibility
        self.description = description
        sub_task_scrubber = _TaskGroupSubTaskScrubber()
        if sub_tasks:
            self.groups: list[TaskGroup] = sub_task_scrubber.scrub_sub_tasks(
                self.name, sub_tasks, TaskGroup)
            self.tasks: list[Task] = sub_task_scrubber.scrub_sub_tasks(
                self.name, sub_tasks, Task)
        else:
            self.groups: list[TaskGroup] = []
            self.tasks: list[Task] = []
        self.notes: NotesList | None = make_list(notes, allow_none=True)
        self.footnotes: NotesDict | None = footnotes
        self.hints: dict = hints

    def copy(self, visibility: int = None) -> Self:
        """Copy this task group.

        Args:
            visibility: optional visibility override

        Returns:
            task group copy
        """
        group_copy = TaskGroup(
            name=self.name,
            sub_tasks=[],
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
        """TaskGroup creation based in raw input data (should be dictionary).

        Recursively creates contained TaskGroup and Task objects.

        Args:
            name: task group name
            raw_data: raw input data

        Returns:
            TaskGroup object
        """
        converter = _TaskTreeElementConverter(raw_data)
        return cls(
            name=name,
            sub_tasks=converter.get_sub_tasks(),
            description=converter.get_description(),
            visibility=converter.get_visibility(),
            notes=converter.get_notes(),
            footnotes=converter.get_footnotes(),
            **converter.get_hints(),
        )

    def dump(self, indent: str = None) -> str:
        """Format data as text block for logging.

        Args:
            indent: indent string if nested

        Returns:
            formatted text block
        """
        if indent is None:
            indent = ''
        group_dump = self.format_dump(
            self.name,
            indent,
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
    """Application task tree.

    For clarity, requires keyword arguments.
    """
    def __init__(self,
                 *,
                 sub_tasks: Sequence[Task | TaskGroup],
                 name: str | None = None,
                 ):
        """TaskGroup constructor.

        Args:
            sub_tasks: nested sub-tasks and or sub-groups
            name: optional task tree name (default: default root task name)
        """
        super().__init__(name=name,
                         sub_tasks=sub_tasks,
                         description='root task',
                         visibility=2)

    def copy(self, visibility: int = None) -> Self:
        """Copy this task group.

        Args:
            visibility: optional visibility override

        Returns:
            task group copy
        """
        tree_copy = TaskTree(
            name=self.name,
            sub_tasks=[],
        )
        tree_copy.tasks = self.tasks.copy()
        tree_copy.groups = self.groups.copy()
        return tree_copy

    @classmethod
    def from_raw_data(cls, name: str, raw_data: Any) -> Self:
        """TaskTree creation based in raw input data (should be dictionary).

        Recursively creates contained TaskGroup and Task objects.

        Args:
            name: task tree name
            raw_data: raw input data

        Returns:
            TaskTree object
        """
        converter = _TaskTreeElementConverter(raw_data)
        task_tree = cls(
            name=name,
            sub_tasks=converter.get_sub_tasks(),
        )
        hints = converter.get_hints()
        if hints:
            log_error('Ignoring unexpected task tree hint keys:', *sorted(hints.keys()))
        return task_tree

    def log_dump_all(self, heading: str = None):
        """Dump task tree to log, e.g. console.

        Args:
            heading: optional heading text
        """
        log_heading(heading or 'task tree', is_error=True)
        log_message(self.dump(), is_error=True)
        log_heading('', is_error=True)


class BuiltinTask(Task):
    """Built-in task reference.

    For clarity, requires keyword arguments.
    """

    def __init__(self,
                 *,
                 name: str,
                 visibility: int = None,
                 ):
        """Built-in task constructor.

        Args:
            name: task name
            visibility: optional visibility override: 0=normal, 1=secondary, 2=hidden
        """
        if name not in BUILTINS:
            abort(f'Unknown built-in task name: {name}')
        builtin_task = BUILTINS[name]
        if not isinstance(builtin_task, Task):
            abort(f'Built-in is not a task: {name}')
        if visibility is None:
            visibility = builtin_task.visibility
        super().__init__(
            name=builtin_task.name,
            impl=builtin_task.impl,
            visibility=visibility,
            description=builtin_task.description,
            notes=builtin_task.notes,
            footnotes=builtin_task.footnotes,
            **builtin_task.hints,
        )

    @classmethod
    def from_raw_data(cls, name: str, raw_data: Any) -> Self:
        """Built-in task creation based in raw input data (should be dictionary).

        Args:
            name: task name
            raw_data: raw input data

        Returns:
            BuiltinTask object
        """
        converter = _TaskTreeElementConverter(raw_data)
        return cls(
             name=name,
             visibility=converter.get_visibility(),
         )


class BuiltinTaskGroup(TaskGroup):
    """Built-in task group reference.

    For clarity, requires keyword arguments.
    """

    def __init__(self,
                 *,
                 name: str,
                 visibility: int = None,
                 ):
        """Built-in task group constructor.

        Args:
            name: task group name
            visibility: optional visibility override: 0=normal, 1=secondary, 2=hidden
        """
        if name not in BUILTINS:
            abort(f'Unknown built-in task name: {name}')
        builtin_task_group = BUILTINS[name]
        if not isinstance(builtin_task_group, TaskGroup):
            abort(f'Built-in is not a task group: {name}')
        if visibility is None:
            visibility = builtin_task_group.visibility
        sub_tasks: list[TaskGroup | Task] = builtin_task_group.groups.copy()
        sub_tasks.extend(builtin_task_group.tasks.copy())
        super().__init__(
            name=builtin_task_group.name,
            sub_tasks=sub_tasks,
            visibility=visibility,
            description=builtin_task_group.description,
            notes=builtin_task_group.notes,
            footnotes=builtin_task_group.footnotes,
            **builtin_task_group.hints,
        )

    @classmethod
    def from_raw_data(cls, name: str, raw_data: Any) -> Self:
        """Built-in task group creation based in raw input data (should be dictionary).

        Args:
            name: task name
            raw_data: raw input data

        Returns:
            BuiltinTaskGroup object
        """
        converter = _TaskTreeElementConverter(raw_data)
        return cls(
             name=name,
             visibility=converter.get_visibility(),
         )


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

    def _get_sub_stack(stack_task: RuntimeTask, sub_names: Sequence[str]):
        for sub_task in stack_task.sub_tasks:
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


def task(
    naked_task_function: TaskFunction = None,
    /,
    description: str = None,
    notes: NotesSpec = None,
    footnotes: NotesDict = None,
) -> TaskFunction:
    """Task function decorator.

    Args:
        naked_task_function: not used explicitly, only non-None for naked @task
            functions
        description: task description (default: parsed from doc string)
        notes: optional note or notes text
        footnotes: optional footnotes dictionary

    Returns:
        wrapper task function
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
                        filter_type: type[T_task_or_group],
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
        self.builtin_regex = re.compile(fr'^{BUILTIN_TASK_NAME_PATTERN}$')

    def _get_raw_data(self, name: str) -> Any | None:
        if name not in self.keys_used:
            self.keys_used.append(name)
        return self.raw_data.get(name)

    def get_name(self) -> str:
        """Convert raw data to name, with handling of unnamed elements.

        Returns:
            name
        """
        raw_data = self._get_raw_data('name')
        if not raw_data:
            self.unnamed_count += 1
            return f'unnamed_{self.unnamed_count}'
        return str(raw_data)

    def get_description(self) -> str | None:
        """Convert raw data to description.

        Returns:
            description or None
        """
        raw_data = self._get_raw_data('description')
        if raw_data is None:
            return None
        if not isinstance(raw_data, str):
            return str(raw_data)
        return raw_data

    def get_visibility(self) -> int:
        """Convert raw data to visibility.

        Returns:
            visibility
        """
        raw_data = self._get_raw_data('visibility')
        if raw_data is None:
            return 0
        if not isinstance(raw_data, int) or raw_data < 0 or raw_data > 2:
            log_error(f'Bad visibility value: {raw_data}')
            return 0
        return raw_data

    def get_notes(self) -> NotesList | None:
        """Convert raw data to notes.

        Returns:
            notes list or None
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
        """Convert raw data to footnotes.

        Returns:
            footnotes dictionary or None
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
        """Extract hints from raw data based on unused dictionary keys.

        Returns:
            hints dictionary
        """
        return {
            name: value
            for name, value in self.raw_data.items()
            if name not in self.keys_used
        }

    def get_sub_tasks(self) -> list[Task | TaskGroup]:
        """Convert raw data to sub_tasks list.

        Returns:
            sub-tasks list
        """
        raw_data = self._get_raw_data('sub_tasks')
        if raw_data is None:
            return []
        if not isinstance(raw_data, dict):
            log_error('Sub-tasks raw data is not a dictionary.')
            return []
        sub_tasks: list[Task | TaskGroup] = []
        for name, raw_item_data in raw_data.items():
            # Check for special built-in task/group name.
            matched_name = self.builtin_regex.match(name)
            if matched_name is not None:
                name = matched_name.group(1)
                if name not in BUILTINS:
                    abort(f'Unknown built-in task or group:'
                          f' {name} ({BUILTIN_TASK_NAME_FORMAT.format(name)})')
                builtin = BUILTINS[name]
                if isinstance(builtin, TaskGroup):
                    sub_tasks.append(BuiltinTaskGroup.from_raw_data(name, raw_item_data))
                else:
                    sub_tasks.append(BuiltinTask.from_raw_data(name, raw_item_data))
            else:
                if isinstance(raw_item_data, dict) and 'sub_tasks' in raw_item_data:
                    sub_tasks.append(TaskGroup.from_raw_data(name, raw_item_data))
                else:
                    sub_tasks.append(Task.from_raw_data(name, raw_item_data))
        return sub_tasks

    def get_impl(self) -> TaskReference | None:
        """Convert raw data to task reference.

        Returns:
            task reference or None
        """
        raw_data = self._get_raw_data('impl')
        if raw_data is None:
            return None
        if not isinstance(raw_data, str) and not ismodule(raw_data) and not isfunction(raw_data):
            log_error(f'Bad task implementation reference: {raw_data}')
            return None
        return raw_data


BUILTINS: dict[str, Task | TaskGroup] = {
    #: Task for "alias" management.
    'alias': Task(
        name='alias',
        cli_options={
            'all': ['-a', '--all'],
            'comment': ['-c', '--comment'],
            'delete': ['-d', '--delete'],
        },
        visibility=1,
    ),

    #: Task group for building a distribution.
    'build': TaskGroup(
        name='build',
        sub_tasks=[
            Task(name='sdist'),
        ],
        visibility=1,
    ),

    #: Task for "help" command.
    'help': Task(
        name='help',
        visibility=1,
        cli_options={'all_tasks': ['-a', '--all']},
    ),

    #: Task group for generating and serving documentation.
    'doc': TaskGroup(
        name='doc',
        sub_tasks=[
            Task(name='html'),
            Task(name='markdown'),
            Task(name='pdf'),
            Task(name='server', cli_options={'port': ['-p', '--port']}),
        ],
        visibility=1,
    ),

    #: Task for parameter management.
    'param': Task(
        name='param',
        cli_options={
            'all': ['-a', '--all'],
            'delete': ['-d', '--delete'],
        },
        visibility=1,
    ),

    #: Task for running unit tests.
    'unittest': Task(
        name='unittest',
        visibility=1,
        cli_options={'name_sort': ['-n', '--name-sort']},
    ),

    #: Task group utility commands.
    'utility': TaskGroup(
        name='utility',
        sub_tasks=[
            Task(name='toml_to_json'),
        ],
        visibility=1,
    ),

    #: Task group for "venv" (virtual environment) sub-commands.
    'venv': TaskGroup(
        name='venv',
        sub_tasks=[
            Task(name='build', cli_options={'rebuild_venv': ['-r', '--rebuild']}),
            Task(name='ipython', cli_trailing='trailing_arguments'),
            Task(name='pip', cli_trailing='trailing_arguments'),
            Task(name='python', cli_trailing='trailing_arguments'),
            Task(name='run', cli_trailing='trailing_arguments'),
            Task(name='update'),
        ],
        visibility=1,
    ),
}
