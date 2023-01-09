# Copyright (C) 2020-2022, Steven Cooper
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

import sys
from dataclasses import dataclass
from inspect import ismodule
from types import ModuleType

from .types import TaskFunction, TaskReference, SubTaskCollection, SubTaskDict
from .util.log import abort
from .util.text.footnotes import NotesSpec, NotesDict


class _HintRegistry:

    _supported_task_hints: set[str] = set()
    _used_task_hints: set[str] = set()
    _supported_field_hints: set[str] = set()
    _used_field_hints: set[str] = set()

    def add_supported_task_hints(self, *names: str):
        """
        Register supported task hint name(s).

        :param names: task hint name(s)
        """
        for name in names:
            self._supported_task_hints.add(name)

    def add_used_task_hints(self, *names: str):
        """
        Register used task hint name(s).

        :param names: task hint name(s)
        """
        for name in names:
            self._used_task_hints.add(name)

    def get_bad_task_hints(self) -> list[str]:
        """
        Get task hints that are used, but unsupported.

        :return: bad task hints list
        """
        return list(sorted(self._used_task_hints.difference(self._supported_task_hints)))

    def add_supported_field_hints(self, *names: str):
        """
        Register supported field hint name(s).

        :param names: field hint name(s)
        """
        for name in names:
            self._supported_field_hints.add(name)

    def add_used_field_hints(self, *names: str):
        """
        Register used field hint name(s).

        :param names: field hint name(s)
        """
        for name in names:
            self._used_field_hints.add(name)

    def get_bad_field_hints(self) -> list[str]:
        """
        Get field hints that are used, but unsupported.

        :return: bad field hints list
        """
        return list(sorted(self._used_field_hints.difference(self._supported_field_hints)))


HINT_REGISTRY = _HintRegistry()


@dataclass
class RegisteredTask:
    """Registered task specification."""
    task_function: TaskFunction
    module: ModuleType
    full_name: str
    description: str | None
    primary_tasks: SubTaskDict | None
    secondary_tasks: SubTaskDict | None
    hidden_tasks: SubTaskDict | None
    notes: NotesSpec | None
    footnotes: NotesDict | None
    driver_hints: dict


TASKS_BY_FUNCTION_ID: dict[int, RegisteredTask] = {}
TASKS_BY_MODULE_ID: dict[int, RegisteredTask] = {}


def task(naked_task_function: TaskFunction = None,
         /,
         description: str = None,
         tasks: SubTaskCollection = None,
         secondary: SubTaskCollection = None,
         hidden: SubTaskCollection = None,
         notes: NotesSpec = None,
         footnotes: NotesDict = None,
         **driver_hints,
         ) -> TaskFunction:
    """
    Task function decorator.

    :param naked_task_function: not used explicitly, only non-None for naked @task functions
    :param description: task description (default: parsed from doc string)
    :param tasks: optional sub-task reference(s) as sequence or dictionary
    :param secondary: optional secondary sub-task reference(s) as sequence or dictionary
    :param hidden: optional hidden sub-task reference(s) as sequence or dictionary
    :param notes: optional note or notes text
    :param footnotes: optional footnotes dictionary
    :param driver_hints: driver hint dictionary
    :return: wrapper task function
    """
    if naked_task_function is None:
        # The decorator was called with parenthesized arguments.
        def _task_function_wrapper(task_function: TaskFunction) -> TaskFunction:
            _register_task_function(
                task_function=task_function,
                description=description,
                primary_tasks=tasks,
                secondary_tasks=secondary,
                hidden_tasks=hidden,
                notes=notes,
                footnotes=footnotes,
                driver_hints=driver_hints,
            )
            return task_function

        return _task_function_wrapper

    # The decorator was invoked "naked", without parentheses or arguments.
    _register_task_function(naked_task_function)
    return naked_task_function


def _register_task_function(
        task_function: TaskFunction,
        description: str | None = None,
        primary_tasks: SubTaskCollection | None = None,
        secondary_tasks: SubTaskCollection | None = None,
        hidden_tasks: SubTaskCollection | None = None,
        notes: NotesSpec = None,
        footnotes: NotesDict = None,
        driver_hints: dict | None = None,
):
    # task_function.__module__ may be None, e.g. for tasks in a Jiig script.
    module_name = getattr(task_function, '__module__')
    if module_name == 'builtins':
        module_name = '<tool>'
    module = sys.modules.get(module_name) if module_name else None
    registered_task = RegisteredTask(
        task_function=task_function,
        module=module,
        full_name=f'{module_name}.{task_function.__name__}()',
        description=description,
        primary_tasks=_make_sub_tasks_map(primary_tasks),
        secondary_tasks=_make_sub_tasks_map(secondary_tasks),
        hidden_tasks=_make_sub_tasks_map(hidden_tasks),
        notes=notes,
        footnotes=footnotes,
        driver_hints=driver_hints or {},
    )
    TASKS_BY_FUNCTION_ID[id(task_function)] = registered_task
    if module is not None:
        TASKS_BY_MODULE_ID[id(registered_task.module)] = registered_task
    if driver_hints:
        HINT_REGISTRY.add_used_task_hints(*driver_hints.keys())


def _get_default_task_name(reference: TaskReference) -> str:
    if ismodule(reference):
        return reference.__name__.split('.')[-1]
    if isinstance(reference, str):
        return reference.split('.')[-1]
    name = reference.__name__
    # Strip trailing underscore, which can be used to avoid collisions with built-ins.
    if name.endswith('_'):
        name = name[:-1]
    return name


def _make_sub_tasks_map(raw_tasks: SubTaskCollection | None) -> SubTaskDict | None:
    # None?
    if raw_tasks is None:
        return None
    # Already a dictionary?
    if isinstance(raw_tasks, dict):
        return raw_tasks
    # Convert sequence to dictionary using default names based on references.
    if isinstance(raw_tasks, (list, tuple)):
        return {_get_default_task_name(reference): reference for reference in raw_tasks}
    abort('Assigned tasks are neither a sequence nor a dictionary.', raw_tasks)
