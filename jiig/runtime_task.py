"""
Registered task.
"""

import re
from dataclasses import dataclass, fields
from typing import Text, Optional, Dict, Type, List, Any, Collection

from jiig.field import ArgumentAdapter
from jiig.registry import TASK_REGISTRY, TaskRegistration
from jiig.util.console import log_error
from jiig.util.footnotes import NotesList, NotesDict
from jiig.util.general import DefaultValue
from jiig.util.repetition import Repetition

TASK_IDENT_REGEX = re.compile(r'^'
                              r'([a-zA-Z][a-zA-Z0-9\-_]*)'
                              r'(?:\[(s|secondary|h|hidden)\])?'
                              r'$')


class RuntimeTask:
    """
    Runtime task data (resolved).

    Resolved tasks are produced dynamically based on static task specifications
    while navigating the task hierarchy.
    """

    @dataclass
    class Field:
        """Post-registration field data."""
        element_type: Any
        field_type: Any
        description: Text
        default: Optional[DefaultValue]
        adapters: List[ArgumentAdapter]
        repeat: Optional[Repetition]
        choices: Optional[Collection]
        hints: Dict

    def __init__(self, task_registration: TaskRegistration, name: Text, visibility: int):
        self._task_registration = task_registration
        self._name = name
        self._visibility = visibility
        # Produced on-demand.
        self._sub_tasks: Optional[Dict[Text, RuntimeTask]] = None
        self._fields: Optional[Dict[Text, RuntimeTask.Field]] = None
        self._handler_class_name: Optional[Text] = None

    @property
    def name(self) -> Text:
        """
        Task name.

        :return: task name
        """
        return self._name

    @property
    def handler_class(self) -> Type:
        """
        Task handler class.

        :return: task handler class
        """
        return self._task_registration.registered_class

    @property
    def handler_class_name(self) -> Text:
        """
        Task handler class name.

        :return: task handler class name
        """
        if self._handler_class_name is None:
            self._handler_class_name = '.'.join([self.handler_class.__module__,
                                                 self.handler_class.__name__])
        return self._handler_class_name

    @property
    def fields(self) -> Dict[Text, Field]:
        """
        Field map indexed by name.

        :return: field map
        """
        if self._fields is None:
            self._fields = {}
            default_values: Dict[Text, DefaultValue] = {}
            try:
                # noinspection PyDataclass
                for field in fields(self.handler_class):
                    default_values[field.name] = DefaultValue.from_dataclass_field(field)
            except TypeError as exc:
                log_error(f'Task handler class {self.handler_class_name}'
                          f' may not be a dataclass.', exc)
            for name, field_spec in self._task_registration.fields.items():
                default = default_values.get(name, None)
                if default is None and 'default' in field_spec.hints:
                    default = DefaultValue(field_spec.hints['default'])
                if 'repeat' in field_spec.hints:
                    repeat = Repetition.from_spec(field_spec.hints['repeat'])
                else:
                    repeat = None
                choices: Optional[List] = field_spec.hints.get('choices', None)
                self._fields[name] = RuntimeTask.Field(
                    element_type=field_spec.element_type,
                    field_type=field_spec.field_type,
                    description=field_spec.description,
                    default=default,
                    adapters=field_spec.adapters,
                    repeat=repeat,
                    choices=choices,
                    hints=field_spec.hints,
                )
        return self._fields

    @property
    def visibility(self) -> int:
        """
        Help visibility, 0=primary, 1=secondary, 2=hidden.

        :return: visibility integer value
        """
        return self._visibility

    @property
    def description(self) -> Text:
        """
        Task description.

        :return: task description
        """
        return self._task_registration.description

    @property
    def notes(self) -> NotesList:
        """
        Task help notes.

        :return: note list
        """
        return self._task_registration.notes

    @property
    def footnotes(self) -> NotesDict:
        """
        Named footnotes displayed in task help if referenced by "[<name>]".

        :return: footnote dictionary
        """
        return self._task_registration.footnotes or {}

    @property
    def sub_tasks(self) -> Dict[Text, 'RuntimeTask']:
        """
        Produce a sub-task list, with added name and visibility.

        :return: sub-task list
        """
        if self._sub_tasks is None:
            self._sub_tasks: Dict[Text, RuntimeTask] = {}
            for ident, task_ref in self._task_registration.tasks.items():
                ident_match = TASK_IDENT_REGEX.match(ident)
                if ident_match is None:
                    log_error(f'Bad task identifier "{ident}".')
                    continue
                name = ident_match.group(1)
                visibility_spec = ident_match.group(2).lower() if ident_match.group(2) else ''
                if visibility_spec in ['s', 'secondary']:
                    visibility = 1
                elif visibility_spec in ['h', 'hidden']:
                    visibility = 2
                else:
                    visibility = 0
                resolved_task = self.resolve(task_ref, name, visibility)
                if resolved_task is not None:
                    self._sub_tasks[resolved_task.name] = resolved_task
        return self._sub_tasks

    @classmethod
    def resolve(cls,
                task_ref: TASK_REGISTRY.Reference,
                name: Text,
                visibility: int,
                ) -> Optional['RuntimeTask']:
        """
        Resolve a task reference (if possible).

        :param task_ref: task reference
        :param name: task name
        :param visibility: visibility, e.g. for help output
        :return: task reference if resolved or None otherwise
        """
        task_registration = TASK_REGISTRY.resolve(task_ref)
        if task_registration is None:
            log_error(f'Bad task "{name}" reference.', task_ref)
            return None
        return RuntimeTask(task_registration, name, visibility)
