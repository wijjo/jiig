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
Task registry.

Uses common Registry support, but adds data to the registration record and
provides a more type-specific API for accessing and querying the registry.
"""
import os
import re
import sys
from dataclasses import dataclass
from inspect import isfunction, ismodule
from typing import Text, Dict, List, Optional, Union, cast, Any, Callable, Sequence, Iterator
from types import ModuleType

from ..util.general import DefaultValue
from ..util.log import log_warning, log_error, abort
from ..util.footnotes import NotesList, NotesDict, FootnoteBuilder
from ..util.python import get_function_fields
from ..util.repetition import Repetition
from ..util.text import plural

from ._registry import RegistrationRecord, Registry
from .context_registry import SelfRegisteringContextBase
from .hint_registry import HINT_REGISTRY
from .field import Field, ArgumentAdapter

DEFAULT_TASK_DESCRIPTION = '(no task description, e.g. in task doc string)'
DEFAULT_FIELD_DESCRIPTION = '(no field description, e.g. in doc string :param:)'
DOC_STRING_PARAM_REGEX = re.compile(r'^\s*:param\s+(\w+)\s*:\s*(.*)\s*$')

# The best we can do for now for a task function type hint, because Callable has
# no syntax for variable keyword arguments.
TaskFunction = Callable
TaskReference = Union[Text, ModuleType, TaskFunction]
SubTaskList = Sequence[TaskReference]
SubTaskDict = Dict[Text, TaskReference]
SubTaskCollection = Union[SubTaskList, SubTaskDict]
TaskImplementation = TaskFunction


@dataclass
class TaskField:
    """Data extracted from task dataclass or task function signature."""
    name: Text
    description: Text
    element_type: Any
    field_type: Any
    default: Optional[DefaultValue]
    repeat: Optional[Repetition]
    choices: Optional[List]
    adapters: List[ArgumentAdapter]


@dataclass
class ParsedDocString:
    """Parsed doc string fields."""
    description: Text
    notes: NotesList
    footnotes: NotesDict
    field_descriptions: Dict[Text, Text]


class TaskRegistrationRecord(RegistrationRecord):
    """
    Task registration record.

    Properties are used for data access for the following reasons:
    - Make data effectively read-only.
    - Provide defaults for None values.
    - Postpone building costly derived data that may not always be needed.
    """

    def __init__(self,
                 implementation: TaskImplementation,
                 module: Optional[ModuleType],
                 primary_tasks: Optional[SubTaskCollection],
                 secondary_tasks: Optional[SubTaskCollection],
                 hidden_tasks: Optional[SubTaskCollection],
                 driver_hints: Optional[Dict],
                 ):
        """
        Task registration constructor.

        :param implementation: task implementation, i.e. function
        :param module: containing module
        :param primary_tasks: primary sub-task references by name
        :param secondary_tasks: secondary sub-task references by name
        :param hidden_tasks: hidden sub-task references by name
        :param driver_hints: additional hints interpreted by the driver
        """
        # noinspection PyUnresolvedReferences
        if module is None and implementation.__module__ is not None:
            # noinspection PyUnresolvedReferences
            module = sys.modules[implementation.__module__]
        super().__init__(implementation, module)
        self.description = None
        self.notes = []
        self.footnotes = {}
        self.primary_tasks = _make_sub_tasks_map(primary_tasks)
        self.secondary_tasks = _make_sub_tasks_map(secondary_tasks)
        self.hidden_tasks = _make_sub_tasks_map(hidden_tasks)
        self.driver_hints = driver_hints or {}
        # Keep track of used task hint names so that a sanity check can be performed later.
        HINT_REGISTRY.add_used_task_hints(*driver_hints.keys())

    @property
    def implementation(self) -> TaskImplementation:
        """
        Registered task implementation.

        :return: implementation reference
        """
        # noinspection PyTypeChecker
        return super().implementation

    def get_tasks(self,
                  exclude_secondary: bool = False,
                  exclude_hidden: bool = False,
                  ) -> Iterator[TaskReference]:
        """
        Iterate all tasks, including primary, secondary, and hidden.

        :param exclude_secondary: omit secondary task references
        :param exclude_hidden: omit hidden task references
        :return: task reference iterator
        """
        if self.primary_tasks:
            for task_reference in self.primary_tasks.values():
                yield task_reference
        if self.secondary_tasks and not exclude_secondary:
            for task_reference in self.secondary_tasks.values():
                yield task_reference
        if self.hidden_tasks and not exclude_hidden:
            for task_reference in self.hidden_tasks.values():
                yield task_reference


def _get_default_task_name(reference: TaskReference) -> Text:
    if ismodule(reference):
        return reference.__name__.split('.')[-1]
    if isinstance(reference, str):
        return reference.split('.')[-1]
    name = reference.__name__
    # Strip trailing underscore, which can be used to avoid collisions with built-ins.
    if name.endswith('_'):
        name = name[:-1]
    return name


def _make_sub_tasks_map(raw_tasks: Optional[SubTaskCollection]) -> Optional[SubTaskDict]:
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


class AssignedTask:
    """
    An assigned task adds a name and visibility to registered task data.

    It also provides access to resolved fields and assigned sub-tasks. Text
    items like description, notes, and footnotes are populated as needed with
    default values.
    """

    def __init__(self,
                 registered_task: TaskRegistrationRecord,
                 name: Text,
                 visibility: int,
                 ):
        """
        Construct sub-task.

        :param registered_task: registered task that owns most of the data and some
                                that it can produce on demand
        :param name: task name
        :param visibility: 0=normal, 1=secondary, 2=hidden
        """
        self._registered_task = registered_task
        self.name = name
        self.visibility = visibility
        self._parsed_doc_string: Optional[ParsedDocString] = None
        self._sub_tasks: Optional[List['AssignedTask']] = None
        self._fields: Optional[List[TaskField]] = None

    @property
    def implementation(self) -> TaskImplementation:
        """
        Task implementation.

        :return: implementation class or function
        """
        return self._registered_task.implementation

    @property
    def module(self) -> ModuleType:
        """
        Task module.

        :return: containing module
        """
        return self._registered_task.module

    @property
    def description(self) -> Text:
        """
        Task description.

        :return: description text
        """
        return (self._registered_task.description
                if self._registered_task.description is not None
                else self.parsed_doc_string.description)

    @property
    def notes(self) -> NotesList:
        """
        Task description.

        :return: description text
        """
        return (self._registered_task.notes if self._registered_task.notes is not None
                else self.parsed_doc_string.notes)

    @property
    def footnotes(self) -> NotesDict:
        """
        Task description.

        :return: description text
        """
        return (self._registered_task.footnotes if self._registered_task.footnotes is not None
                else self.parsed_doc_string.footnotes)

    @property
    def sub_tasks(self) -> List['AssignedTask']:
        """
        Assigned sub-task list.

        :return: sub-task list
        """
        if self._sub_tasks is None:
            self._sub_tasks: List[AssignedTask] = []
            if self._registered_task.primary_tasks:
                for name, task_ref in self._registered_task.primary_tasks.items():
                    task = TASK_REGISTRY.resolve_assigned_task(task_ref, name, 0, required=True)
                    self._sub_tasks.append(task)
            if self._registered_task.secondary_tasks:
                for name, task_ref in self._registered_task.secondary_tasks.items():
                    task = TASK_REGISTRY.resolve_assigned_task(task_ref, name, 1, required=True)
                    self._sub_tasks.append(task)
            if self._registered_task.hidden_tasks:
                for name, task_ref in self._registered_task.hidden_tasks.items():
                    task = TASK_REGISTRY.resolve_assigned_task(task_ref, name, 2, required=True)
                    self._sub_tasks.append(task)
        return self._sub_tasks

    @property
    def fields(self) -> List[TaskField]:
        """
        Fields and defaults for task.

        :return: task fields and defaults object
        """
        if self._fields is None:
            if not isfunction(self.implementation):
                abort(f'Task implementation is not a @task function.', self.implementation)
            extracted_fields = get_function_fields(self.implementation)
            errors = extracted_fields.errors
            if (len(extracted_fields.fields) == 0
                    or not issubclass(extracted_fields.fields[0].type_hint,
                                      SelfRegisteringContextBase)):
                abort(f'Task function first argument is not a context.',
                      self.implementation)
            raw_fields = extracted_fields.fields[1:]
        # noinspection PyUnboundLocalVariable
            if errors:
                # noinspection PyUnboundLocalVariable
                abort(f'Bad task {self.full_name} {plural("field", errors)}.', *errors)
            task_fields: List[TaskField] = []
            # noinspection PyUnboundLocalVariable
            for raw_field in raw_fields:
                description = self.parsed_doc_string.field_descriptions.get(raw_field.name)
                if description is None:
                    description = raw_field.annotation.description
                if not isinstance(raw_field.annotation, Field):
                    abort(f'Not all fields in task {self.full_name} have Jiig field hints.')
                task_fields.append(
                    TaskField(raw_field.name,
                              description,
                              raw_field.type_hint,
                              raw_field.annotation.field_type,
                              raw_field.default,
                              raw_field.annotation.repeat,
                              raw_field.annotation.choices,
                              raw_field.annotation.adapters),
                )
            self._fields = task_fields
        return self._fields

    @property
    def full_name(self):
        """
        Full display name.

        :return: full display name
        """
        return self._registered_task.full_name

    @property
    def parsed_doc_string(self) -> ParsedDocString:
        if self._parsed_doc_string is None:
            self._parsed_doc_string = _parse_doc_string(self.implementation)
        return self._parsed_doc_string

    @property
    def hints(self) -> Dict:
        """
        Task hints for driver.

        :return: hint dictionary
        """
        return self._registered_task.driver_hints


class TaskRegistry(Registry):
    """Task registry."""

    def __init__(self):
        """Task registry constructor."""
        super().__init__('task')

    def register(self, registration: TaskRegistrationRecord):
        """
        Perform task registration.

        :param registration: task registration record
        """
        super().register(registration)

    def resolve(self,
                reference: TaskReference,
                required: bool = False,
                ) -> Optional[TaskRegistrationRecord]:
        """
        Resolve task reference to registration record (if possible).

        Use resolve_assigned_task() instead of resolve() when a task has been
        assigned a name and visibility in the context of a tool or parent task.

        :param reference: module, class, or function reference
        :param required: abort if reference resolution fails
        :return: registration record or None if it couldn't be resolved
        """
        return super().resolve(reference, required=required)

    def resolve_assigned_task(self,
                              reference: TaskReference,
                              name: Text,
                              visibility: int,
                              required: bool = False,
                              ) -> Optional[AssignedTask]:
        """
        Resolve task reference to an AssignedTask (if possible).

        Needed as front end to resolve() method in order to merge data from
        registered task with name and visibility when task has been assigned to
        a tool or parent task.

        :param reference: module, class, or function reference
        :param name: task name
        :param visibility: visibility (0=normal, 1=secondary, 2=hidden)
        :param required: abort if reference resolution fails
        :return: resolved task or None if it wasn't resolved and required is False
        """
        registered_task = self.resolve(reference, required=required)
        # noinspection PyTypeChecker
        return AssignedTask(registered_task, name or '', visibility)

    def is_registered(self, reference: TaskReference) -> bool:
        """
        Test if task reference is registered.

        :param reference: task reference to test
        :return: True if the task reference is registered
        """
        return super().is_registered(reference)

    def guess_root_task_implementation(self,
                                       *additional_packages: str,
                                       ) -> Optional[TaskImplementation]:
        """
        Attempt to guess the root task by finding one with no references.

        The main point is to support the quick start use case, and is not
        intended for long-lived projects. It has the following caveats.

        CAVEAT 1: It produces a heuristic guess (not perfect).
        CAVEAT 2: It is quite inefficient, O(N^2), for large numbers of tasks.
        CAVEAT 3: It only works with registered tasks, and won't find non-loaded ones.

        Caveats aside, it prefers to fail, rather than return a bad root task.

        :param additional_packages: additional package names for resolving named modules
        :return: root task implementation if found, None if not
        """

        # Gather the full initial candidate pool.
        candidates_by_id: Dict[int, TaskRegistrationRecord] = {}
        candidate_ids_by_module_name: Dict[Text, int] = {}
        for item_id, registration in self.by_id.items():
            if (not registration.implementation.__module__
                    or not registration.implementation.__module__.startswith('jiig.')):
                # Need to cast to TaskRegistrationRecord (also below).
                candidates_by_id[item_id] = cast(TaskRegistrationRecord, registration)
                candidate_ids_by_module_name[registration.implementation.__module__] = item_id
        if len(candidates_by_id) > 20:
            log_warning('Larger projects should declare an explicit root task.')

        # Reduce candidate pool by looking for references to candidates.
        for registration in self.by_id.values():
            # Remove any candidates that are referenced. Handle module
            # instances, module strings, and function references.
            task_registration = cast(TaskRegistrationRecord, registration)
            for reference in task_registration.get_tasks():
                # Module name?
                if isinstance(reference, str):
                    reference_id = candidate_ids_by_module_name.get(reference)
                    if reference_id is None:
                        for package in additional_packages:
                            module_name = '.'.join([package, reference])
                            reference_id = candidate_ids_by_module_name.get(module_name)
                            if reference_id is not None:
                                break
                # Module instance?
                elif ismodule(reference):
                    reference_id = candidate_ids_by_module_name.get(reference.__name__)
                # @task function?
                else:
                    reference_id = id(reference)
                if reference_id is not None and reference_id in candidates_by_id:
                    del candidates_by_id[reference_id]

        # Wrap-up.
        if len(candidates_by_id) == 0:
            log_error('Root task not found.')
            return None
        if len(candidates_by_id) != 1:
            names = sorted([candidate.full_name for candidate in candidates_by_id.values()])
            log_error(f'More than one root task candidate.', *names)
            return None
        return list(candidates_by_id.values())[0].implementation


TASK_REGISTRY = TaskRegistry()


def _parse_doc_string(implementation: TaskImplementation) -> ParsedDocString:
    footnote_builder = FootnoteBuilder()
    doc_string = implementation.__doc__ or ''
    # Pull out and parse `:param <name>: description` items from the doc string.
    non_param_lines: List[Text] = []
    field_descriptions: Dict[Text, Text] = {}
    param_name: Optional[Text] = None
    for line in doc_string.split(os.linesep):
        param_matched = DOC_STRING_PARAM_REGEX.match(line)
        if param_matched:
            param_name, param_description = param_matched.groups()
            field_descriptions[param_name] = param_description
        else:
            stripped_line = line.strip()
            if stripped_line:
                if param_name:
                    field_descriptions[param_name] += ' ' + stripped_line
            else:
                param_name = None
        if not param_name:
            non_param_lines.append(line)
    # Parse the non-param lines to get the description, notes, and footnotes.
    doc_string = os.linesep.join(non_param_lines)
    footnote_builder.parse(doc_string)
    description = DEFAULT_TASK_DESCRIPTION
    notes: NotesList = []
    for paragraph_idx, paragraph in enumerate(footnote_builder.original_body_paragraphs):
        if paragraph_idx == 0:
            description = paragraph
        else:
            notes.append(paragraph)
    return ParsedDocString(description,
                           notes,
                           footnote_builder.footnotes,
                           field_descriptions)
