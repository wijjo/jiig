"""
Registered task.
"""

import re
from dataclasses import fields
from importlib import import_module
from inspect import isclass, ismodule
from typing import Text, Optional, Dict, Type, List

from jiig.registry import TaskReference
from jiig.util.console import log_error
from jiig.util.footnotes import NotesList, NotesDict
from jiig.util.general import DefaultValue
from jiig.util.repetition import Repetition

from .runtime_field import RuntimeField
from jiig.registry.task_registry import TaskRegistry
from jiig.registry.task_specification import TaskSpecification

TASK_IDENT_REGEX = re.compile(r'^'
                              r'([a-zA-Z][a-zA-Z0-9\-_]*)'
                              r'(?:\[(s|secondary|h|hidden)\])?'
                              r'$')


class RuntimeTask:
    """
    Resolved task data.

    Resolved tasks are produced dynamically based on static task specifications
    while navigating the task hierarchy.
    """

    def __init__(self, spec: TaskSpecification, name: Text, visibility: int):
        self._spec = spec
        self._name = name
        self._visibility = visibility
        # Produced on-demand.
        self._sub_tasks: Optional[Dict[Text, RuntimeTask]] = None
        self._fields: Optional[Dict[Text, RuntimeField]] = None
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
        return self._spec.handler_class

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
    def fields(self) -> Dict[Text, RuntimeField]:
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
            for name, field_spec in self._spec.fields.items():
                default = default_values.get(name, None)
                if default is None and 'default' in field_spec.hints:
                    default = DefaultValue(field_spec.hints['default'])
                if 'repeat' in field_spec.hints:
                    repeat = Repetition.from_spec(field_spec.hints['repeat'])
                else:
                    repeat = None
                choices: Optional[List] = field_spec.hints.get('choices', None)
                self._fields[name] = RuntimeField(
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
        return self._spec.description

    @property
    def notes(self) -> NotesList:
        """
        Task help notes.

        :return: note list
        """
        return self._spec.notes

    @property
    def footnotes(self) -> NotesDict:
        """
        Named footnotes displayed in task help if referenced by "[<name>]".

        :return: footnote dictionary
        """
        return self._spec.footnotes or {}

    @property
    def sub_tasks(self) -> Dict[Text, 'RuntimeTask']:
        """
        Produce a sub-task list, with added name and visibility.

        :return: sub-task list
        """
        if self._sub_tasks is None:
            self._sub_tasks: Dict[Text, RuntimeTask] = {}
            for ident, task_ref in self._spec.tasks.items():
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
                runtime_task = self.resolve(task_ref, name, visibility)
                if runtime_task is not None:
                    self._sub_tasks[runtime_task.name] = runtime_task
        return self._sub_tasks

    @classmethod
    def resolve(cls,
                task_ref: TaskReference,
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
        # Reference is a class? Hopefully it's one that was registered.
        if isclass(task_ref):
            task_spec = TaskRegistry.by_class_id.get(id(task_ref))
            if task_spec is None:
                log_error(f'Task class {task_ref.__name__} is not registered.')
                return None
            return RuntimeTask(task_spec, name, visibility)
        # Reference is a module name? Convert the reference to a loaded module.
        if isinstance(task_ref, str):
            try:
                task_ref = import_module(task_ref)
            except Exception as exc:
                log_error(f'Failed to load task module.',
                          exc, module_name=task_ref, exception_traceback=True)
                return None
        # Reference is a module? Hopefully it's one that was registered.
        if ismodule(task_ref):
            task_spec = TaskRegistry.by_module_id.get(id(task_ref))
            if task_spec is None:
                log_error(f'Failed to resolve unregistered task module'
                          f' {task_ref.__name__} (id={id(task_ref)}).')
                return None
            return RuntimeTask(task_spec, name, visibility)
        log_error(f'Bad task "{name}" reference.', task_ref)
        return None
