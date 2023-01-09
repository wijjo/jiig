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

"""Runtime task."""

import os
import re
import sys
from dataclasses import dataclass
from importlib import import_module
from inspect import isfunction, ismodule
from types import ModuleType
from typing import Self, Any

from jiig.field import Field
from jiig.runtime import Runtime
from jiig.task import TASKS_BY_FUNCTION_ID, TASKS_BY_MODULE_ID
from jiig.types import ArgumentAdapter, TaskFunction, TaskReference, SubTaskDict
from jiig.util.default import DefaultValue
from jiig.util.log import abort, log_error, log_message
from jiig.util.python import get_function_fields
from jiig.util.repetition import Repetition
from jiig.util.text.footnotes import NotesList, NotesDict, FootnoteBuilder

DEFAULT_TASK_DESCRIPTION = '(no task description, e.g. in task doc string)'
DEFAULT_FIELD_DESCRIPTION = '(no field description, e.g. in doc string :param:)'
DOC_STRING_PARAM_REGEX = re.compile(r'^\s*:param\s+(\w+)\s*:\s*(.*)\s*$')


@dataclass
class TaskField:
    """Data extracted from task dataclass or task function signature."""
    name: str
    description: str
    element_type: Any
    field_type: Any
    default: DefaultValue | None
    repeat: Repetition | None
    choices: list | None
    adapters: list[ArgumentAdapter]


@dataclass
class ParsedDocString:
    """Parsed doc string fields."""
    description: str
    notes: NotesList
    footnotes: NotesDict
    field_descriptions: dict[str, str]


class RuntimeTask:
    """
    Runtime task information, based on a registered class.

    Also provides access to resolved fields and sub-tasks.

    Text items like description, notes, and footnotes are populated as needed
    with default values.
    """
    def __init__(self,
                 name: str,
                 full_name: str,
                 visibility: int,
                 task_function: TaskFunction,
                 module: ModuleType | None,
                 description: str,
                 primary_tasks: SubTaskDict | None,
                 secondary_tasks: SubTaskDict | None,
                 hidden_tasks: SubTaskDict | None,
                 notes: NotesList,
                 footnotes: NotesDict,
                 driver_hints: dict,
                 field_descriptions: dict[str, str],
                 ):
        """
        Construct sub-task.

        :param name: task name
        :param full_name: fully-qualified task name
        :param visibility: 0=normal, 1=secondary, 2=hidden
        :param task_function: task implementation function
        """
        self.name = name
        self.full_name = full_name
        self.visibility = visibility
        self.task_function = task_function
        self.module = module
        self.description = description
        self.primary_tasks = primary_tasks
        self.secondary_tasks = secondary_tasks
        self.hidden_tasks = hidden_tasks
        self.notes = notes
        self.footnotes = footnotes
        self.driver_hints = driver_hints
        self.field_descriptions = field_descriptions
        self._sub_tasks: list[Self] | None = None
        self._fields: list[TaskField] | None = None

    @property
    def sub_tasks(self) -> list[Self]:
        """
        Produce sub-task list.

        :return: sub-task list
        """
        if self._sub_tasks is None:
            self._sub_tasks: list[RuntimeTask] = []
            if self.primary_tasks is not None:
                for name, task_ref in self.primary_tasks.items():
                    task = self.resolve(task_ref, name, 0, required=True)
                    self._sub_tasks.append(task)
            if self.secondary_tasks is not None:
                for name, task_ref in self.secondary_tasks.items():
                    task = self.resolve(task_ref, name, 1, required=True)
                    self._sub_tasks.append(task)
            if self.hidden_tasks is not None:
                for name, task_ref in self.hidden_tasks.items():
                    task = self.resolve(task_ref, name, 2, required=True)
                    self._sub_tasks.append(task)
        return self._sub_tasks

    @property
    def fields(self) -> list[TaskField]:
        """
        Fields and defaults for task.

        :return: task fields and defaults object
        """
        def _fatal_error(message: str, *args, **kwargs):
            abort(f'Task: {self.full_name}: {message}.', *args, **kwargs)

        if self._fields is None:
            if not isfunction(self.task_function):
                _fatal_error('implementation object is not a function')
            extracted_fields = get_function_fields(self.task_function)
            errors = extracted_fields.errors
            if len(extracted_fields.fields) == 0:
                _fatal_error('there are no arguments/fields')
            if not issubclass(extracted_fields.fields[0].type_hint, Runtime):
                _fatal_error(f'argument #1 is not of type Runtime:'
                             f' {extracted_fields.fields[0].type_hint}')
            raw_fields = extracted_fields.fields[1:]
            if errors:
                _fatal_error('field errors:', *errors)
            task_fields: list[TaskField] = []
            for raw_field in raw_fields:
                description = self.field_descriptions.get(raw_field.name)
                if description is None:
                    description = raw_field.annotation.description
                if not isinstance(raw_field.annotation, Field):
                    _fatal_error(f'field is not a Jiig field hint:'
                                 f' {raw_field.annotation.__class__.__name__}')
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

    @classmethod
    def resolve(cls,
                reference: TaskReference,
                name: str,
                visibility: int,
                required: bool = False,
                ) -> Self | None:
        """
        Resolve task reference to an RuntimeTask (if possible).

        :param reference: module, class, or function reference
        :param name: task name
        :param visibility: visibility (0=normal, 1=secondary, 2=hidden)
        :param required: abort if not resolved
        :return: resolved task or None if it wasn't resolved and required is False
        """
        def _error(*args, **kwargs):
            if required:
                abort(*args, **kwargs)
            else:
                log_error(*args, **kwargs)

        # Resolve string (module package name) reference to loaded module?
        if isinstance(reference, str):
            try:
                reference = import_module(reference)
            except ModuleNotFoundError as exc:
                log_message(f'Python path: {sys.path}')
                _error(f'Failed to import task module: {reference}',
                       exc,
                       exception_traceback=True,
                       exception_traceback_skip=2,
                       skip_non_source_frames=True)
                return None
            except Exception as exc:
                _error(f'Failed to load task module: {reference}',
                       exc,
                       exception_traceback=True,
                       exception_traceback_skip=2,
                       skip_non_source_frames=True)
                return None
        # Resolve module reference?
        if ismodule(reference):
            registered_task = TASKS_BY_MODULE_ID.get(id(reference))
        # Resolve item reference (i.e. class or function)?
        else:
            registered_task = TASKS_BY_FUNCTION_ID.get(id(reference))
        if registered_task is None:
            _error(f'Failed to resolve registered task: {reference.__name__}')
            return None

        module = registered_task.module
        if registered_task.module is None:
            module_name = getattr(registered_task.task_function, '__module__')
            if module_name:
                module = sys.modules[module_name]

        parsed_doc_string: ParsedDocString = _parse_doc_string(registered_task.task_function)
        if registered_task.description is not None:
            description = registered_task.description
        else:
            description = parsed_doc_string.description
        if registered_task.notes is not None:
            notes = registered_task.notes
        else:
            notes = parsed_doc_string.notes
        if registered_task.footnotes is not None:
            footnotes = registered_task.footnotes
        else:
            footnotes = parsed_doc_string.footnotes

        return RuntimeTask(name=name or '',
                           full_name=registered_task.full_name,
                           visibility=visibility,
                           task_function=registered_task.task_function,
                           module=module,
                           description=description,
                           primary_tasks=registered_task.primary_tasks,
                           secondary_tasks=registered_task.secondary_tasks,
                           hidden_tasks=registered_task.hidden_tasks,
                           notes=notes,
                           footnotes=footnotes,
                           driver_hints=registered_task.driver_hints,
                           field_descriptions=parsed_doc_string.field_descriptions,
                           )


def _parse_doc_string(task_function: TaskFunction) -> ParsedDocString:
    footnote_builder = FootnoteBuilder()
    doc_string = task_function.__doc__ or ''
    # Pull out and parse `:param <name>: description` items from the doc string.
    non_param_lines: list[str] = []
    field_descriptions: dict[str, str] = {}
    param_name: str | None = None
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
