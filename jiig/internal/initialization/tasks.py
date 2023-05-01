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

"""Task tree initialization."""

import os
import re
from dataclasses import dataclass
from inspect import (
    isfunction,
    ismodule,
)
from types import ModuleType
from typing import Sequence

from jiig.builtins import BUILTINS
from jiig.fields import (
    TaskField,
    Field,
)
from jiig.runtime import Runtime
from jiig.task import (
    TASKS_BY_FUNCTION_ID,
    TASKS_BY_MODULE_ID,
    RegisteredTask,
    RuntimeTask,
    Task,
    TaskGroup,
    TaskTree,
)
from jiig.types import (
    ModuleReference,
    TaskFunction,
)
from jiig.util.log import (
    abort,
    log_error,
)
from jiig.util.options import OPTIONS
from jiig.util.python import (
    ModuleReferenceResolver,
    get_function_fields,
)
from jiig.util.text.footnotes import (
    NotesList,
    NotesDict,
    FootnoteBuilder,
)

from .tool_environment import ToolEnvironment

DEFAULT_TASK_DESCRIPTION = '(no task description, e.g. in task doc string)'
DEFAULT_FIELD_DESCRIPTION = '(no field description, e.g. in doc string :param:)'
DOC_STRING_PARAM_REGEX = re.compile(r'^\s*:param\s+(\w+)\s*:\s*(.*)\s*$')


def prepare_tasks(
    task_tree: TaskTree,
    tool_env: ToolEnvironment,
) -> RuntimeTask:
    """Prepare runtime task tree.

    Args:
        task_tree: raw input task tree
        tool_env: tool environment data

    Returns:
        runtime task tree root
    """
    if OPTIONS.debug:
        task_tree.log_dump_all()

    # Build runtime task hierarchy.
    preparer = _RuntimeTaskPreparer(task_tree,
                                    tool_env.tool_tasks_package,
                                    tool_env.jiig_tasks_package)
    return preparer.populate()


@dataclass
class _DocData:
    description: str
    notes: NotesList
    footnotes: NotesDict
    field_descriptions: dict[str, str]


class _RuntimeTaskPreparer:

    def __init__(self,
                 task_tree: TaskTree,
                 tasks_package: ModuleType,
                 jiig_tasks_package: ModuleType | None,
                 ):
        self.task_tree = task_tree
        self.tasks_package = tasks_package
        self.jiig_tasks_package = jiig_tasks_package
        self.module_resolver = ModuleReferenceResolver()

    def populate(self) -> RuntimeTask:
        """Convert configuration TaskTree tasks to complete RuntimeTask hierarchy."""
        doc_string = self.get_package_doc_string(self.tasks_package)
        doc_data = self.parse_doc_string(
            doc_string,
            self.task_tree.description,
            self.task_tree.notes,
            self.task_tree.footnotes,
        )
        root_task = RuntimeTask.new_tree(
            description=doc_data.description,
            sub_tasks=[],
            notes=doc_data.notes,
            footnotes=doc_data.footnotes,
            hints=self.task_tree.hints,
        )
        self.populate_task_group(self.task_tree, self.tasks_package, root_task)
        return root_task

    def populate_task_group(self,
                            task_group: TaskGroup,
                            package: ModuleReference | None,
                            runtime_task_group: RuntimeTask,
                            *names: str):
        """Convert configuration TaskGroup tasks to RuntimeTask hierarchy."""
        for sub_task in task_group.tasks:
            runtime_sub_task = self._new_task(
                sub_task,
                task_group,
                package,
                names,
            )
            if runtime_sub_task is not None:
                runtime_task_group.sub_tasks.append(runtime_sub_task)
        for sub_group in task_group.groups:
            sub_package = self.get_sub_package_reference(package, sub_group.name)
            runtime_sub_group = self._new_group(
                sub_group,
                sub_package,
                names,
            )
            runtime_task_group.sub_tasks.append(runtime_sub_group)
            self.populate_task_group(
                sub_group,
                sub_package,
                runtime_sub_group,
                *names,
                sub_group.name,
            )
        runtime_task_group.sub_tasks.sort(key=lambda t: t.name)

    def _new_task(self,
                  task: Task,
                  task_group: TaskGroup,
                  package: ModuleReference | None,
                  names: Sequence[str],
                  ) -> RuntimeTask | None:
        registered_task = self.resolve_registered_task(
            task_group,
            package,
            task,
            default_description=task.description,
            default_notes=task.notes,
            default_footnotes=task.footnotes,
        )
        if registered_task is None:
            return None
        doc_data = self.parse_doc_string(
            registered_task.task_function.__doc__ or '',
            registered_task.description,
            registered_task.notes,
            registered_task.footnotes,
        )
        full_name = '.'.join(list(names) + [task.name])
        fields = self.get_fields(full_name,
                                 registered_task.task_function,
                                 doc_data.field_descriptions)
        return RuntimeTask.new_task(
            name=task.name,
            full_name=full_name,
            description=doc_data.description,
            task_function=registered_task.task_function,
            module=registered_task.module,
            fields=fields,
            visibility=task.visibility,
            notes=doc_data.notes,
            footnotes=doc_data.footnotes,
            hints=task.hints,
        )

    def _new_group(self,
                   group: TaskGroup,
                   package: ModuleReference,
                   names: Sequence[str],
                   ) -> RuntimeTask:
        doc_data = self.parse_doc_string(
            self.get_package_doc_string(package),
            group.description,
            group.notes,
            group.footnotes,
        )
        return RuntimeTask.new_group(
            name=group.name,
            full_name='.'.join(list(names) + [group.name]),
            description=doc_data.description,
            visibility=group.visibility,
            sub_tasks=[],
            notes=doc_data.notes,
            footnotes=doc_data.footnotes,
            hints=group.hints,
        )

    def get_package_doc_string(self, package: ModuleReference) -> str:
        if package is None:
            return ''
        module = self.module_resolver.resolve(package)
        return (module.__doc__ or '') if module is not None else ''

    @staticmethod
    def parse_doc_string(doc_string: str | None,
                         app_description: str | None,
                         app_notes: NotesList | None,
                         app_footnotes: NotesDict | None,
                         ) -> _DocData:
        if doc_string is None:
            doc_string = ''
        footnote_builder = FootnoteBuilder()
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
        if app_description is not None:
            description = app_description
        elif footnote_builder.original_body_paragraphs:
            description = footnote_builder.original_body_paragraphs[0]
        else:
            description = DEFAULT_TASK_DESCRIPTION
        if app_notes is not None:
            notes = app_notes
        else:
            notes = footnote_builder.original_body_paragraphs[1:]
        if app_footnotes is not None:
            footnotes = app_footnotes
        else:
            footnotes = footnote_builder.footnotes
        return _DocData(description,
                        notes,
                        footnotes,
                        field_descriptions)

    @staticmethod
    def get_fields(full_name: str,
                   task_function: TaskFunction,
                   field_descriptions: dict[str, str],
                   ) -> list[TaskField]:
        def _fatal_error(message: str, *args, **kwargs):
            abort(f'Task: {full_name}: {message}.', *args, **kwargs)

        if not isfunction(task_function):
            _fatal_error('implementation object is not a function')
        extracted_fields = get_function_fields(task_function)
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
            description = field_descriptions.get(raw_field.name)
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
        return task_fields

    def get_sub_package_reference(self,
                                  package: ModuleReference | None,
                                  name: str,
                                  ) -> str | None:
        if package:
            # Resolve built-in tasks used by external tool with the Jiig package.
            if self.jiig_tasks_package is not None and name in BUILTINS:
                package = self.jiig_tasks_package
            if ismodule(package):
                return '.'.join([package.__name__, name])
            if isinstance(package, str):
                return '.'.join([package, name])
        return None

    def resolve_registered_task(self,
                                task_group: TaskGroup,
                                package: ModuleReference | None,
                                task: Task,
                                default_description: str = None,
                                default_notes: NotesList = None,
                                default_footnotes: NotesDict = None,
                                ) -> RegisteredTask | None:
        if task.impl is not None:
            reference = task.impl
        else:
            reference = self.get_sub_package_reference(package, task.name)
        if reference is None:
            log_error('Task implementation reference can not be resolved.',
                      reference=reference,
                      task_group=task_group.name,
                      task=task.name,
                      package=package)
            return None
        if isfunction(reference):
            module = None
            registered_task = TASKS_BY_FUNCTION_ID.get(id(reference))
        else:
            module = self.module_resolver.resolve(reference)
            if module is None:
                return None
            registered_task = TASKS_BY_MODULE_ID.get(id(module))
        if registered_task is None:
            log_error('Failed to resolve registered task.',
                      task_group=task_group.name,
                      task=task.name,
                      package=package,
                      reference=reference,
                      module=module)
            return None
        # Apply defaults to missing text.
        if registered_task.description is None:
            registered_task.description = default_description
        if registered_task.notes is None:
            registered_task.notes = default_notes
        if registered_task.footnotes is None:
            registered_task.footnotes = default_footnotes
        return registered_task
