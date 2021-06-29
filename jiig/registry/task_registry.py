"""
Task registry.
"""

import os
from dataclasses import dataclass, is_dataclass
from inspect import isclass
from typing import Text, Dict, Type, get_type_hints, get_args, List, Union, TypeVar, Optional

from jiig.field import Field
from jiig.util.log import log_warning, log_error
from jiig.util.footnotes import NotesList, NotesDict

from ._registry import Registration, Registry

T_task = TypeVar('T_task')
TaskReference = Union[Type['RegisteredTask'], Text, object]

DEFAULT_TASK_DESCRIPTION = '(no description, e.g. in task doc string)'


def _full_task_name(task_class: Type[T_task]) -> str:
    module_name = task_class.__module__
    if module_name == 'builtins':
        module_name = '<tool>'
    return f'{module_name}.{task_class.__name__}'


class TaskRegistration(Registration[T_task]):
    """Registered task."""

    # TODO: Can Registration[T_task].Reference be used for `tasks` type hint?
    def __init__(self,
                 handler_class: Type[T_task],
                 description: Text,
                 notes: NotesList,
                 footnotes: NotesDict,
                 tasks: Dict[Text, Union[Type[T_task], Text, object]],
                 fields: Dict[Text, Field],
                 visibility: int,
                 ):
        """
        Registered task constructor.

        :param handler_class: task handler class
        :param description: task description
        :param notes: task help notes
        :param footnotes: named footnotes displayed in task help if referenced by "[<name>]"
        :param tasks: sub-task references by name
        :param fields: argument/option field definition dictionary
        :param visibility: visibility, e.g. in help, with 0=normal, 1=secondary, 2=hidden
        """
        super().__init__(handler_class)
        self.description = description
        self.notes = notes
        self.footnotes = footnotes
        self.tasks = tasks
        self.fields = fields
        self.visibility = visibility

    @property
    def full_name(self) -> str:
        """
        Full class name, including package.

        :return: full class name
        """
        return _full_task_name(self.registered_class)


class RegisteredTask:
    """
    Base Task handler (call-back class).

    Use as a base for registered task classes. It provides type-checked method
    overrides and automatic class registration and wrapping as a dataclass.

    Self-registers to the task registry.

    Also accepts an `skip_registration` boolean keyword to flag a base class
    that should not itself be registered as a RegisteredTask sub-class.

    The class declaration accepts the following keyword arguments:
        - description: task description
        - notes: notes list
        - footnotes: footnotes dictionary
        - tasks: sub-tasks dictionary
        - visibility: 0=normal, 1=secondary, 2=hidden
    """
    def __init_subclass__(cls, /,
                          description: Text = None,
                          notes: NotesList = None,
                          footnotes: NotesDict = None,
                          tasks: Dict[Text, TaskReference] = None,
                          visibility: int = None,
                          **kwargs):
        """Detect and register subclasses."""
        skip_registration = kwargs.pop('skip_registration', False)
        super().__init_subclass__(**kwargs)
        if not skip_registration:
            register_task(cls,
                          description=description,
                          notes=notes,
                          footnotes=footnotes,
                          tasks=tasks,
                          visibility=visibility)


class TaskRegistry(Registry[TaskRegistration, RegisteredTask]):
    """Registered tasks indexed by module and class ID."""
    pass


TASK_REGISTRY = TaskRegistry('task')


def register_task(cls: Type[T_task],
                  description: Text = None,
                  notes: NotesList = None,
                  footnotes: NotesDict = None,
                  tasks: Dict[Text, TaskRegistry.Reference] = None,
                  visibility: int = None,
                  ) -> Type[T_task]:
    """
    Register task class.

    Should not need to call directly. Classes derived from jiig.Task are
    automatically registered.

    :param cls: Task class
    :param description: task description
    :param notes: task help notes
    :param footnotes: named footnotes displayed in task help if referenced by "[<name>]"
    :param tasks: sub-task classes, modules, or module full name, by name
    :param visibility: 0=normal, 1=secondary, 2=hidden
    """
    # The doc string can provide a default description and or notes.
    doc_string_lines: List[Text] = []
    if cls.__doc__ is not None:
        doc_string = cls.__doc__.strip()
        doc_string_lines.extend(doc_string.split(os.linesep))
    # Make sure there's a description.
    if not description:
        if doc_string_lines:
            description = doc_string_lines[0]
        else:
            description = DEFAULT_TASK_DESCRIPTION
    # Make sure there's a notes list, even if empty.
    if notes is None:
        notes: NotesList = []
    if not notes:
        new_note = True
        for note_line in doc_string_lines[1:]:
            note_line = note_line.strip()
            if note_line:
                if new_note:
                    notes.append(note_line)
                    new_note = False
                else:
                    notes[-1] = os.linesep.join([notes[-1], note_line])
            else:
                new_note = True
    # Make sure there's a footnotes dict, even if empty.
    if footnotes is None:
        footnotes: NotesDict = {}
    # Make sure there's a good tasks dict, even if empty.
    if tasks is None:
        tasks = {}
    elif not isinstance(tasks, dict):
        log_error(f'Task class tasks member is not a dict: {_full_task_name(cls.__name__)}')
        tasks = {}
    # Wrap the class in a dataclass.
    if is_dataclass(cls):
        dataclass_class = cls
    else:
        dataclass_class = dataclass(cls)
    # Populate field specifications dict based on annotated class members.
    fields: Dict[Text, Field] = {}
    for name, type_hint in get_type_hints(dataclass_class, include_extras=True).items():
        hint_parts = get_args(type_hint)
        # field.<type>(...) Annotated hints have a field type and FieldSpecification.
        if len(hint_parts) == 2 and isinstance(hint_parts[1], Field):
            fields[name] = hint_parts[1]
    # Build the final option map by converting flags to lists.
    task_registration = TaskRegistration(handler_class=dataclass_class,
                                         description=description,
                                         notes=notes,
                                         footnotes=footnotes,
                                         tasks=tasks,
                                         fields=fields,
                                         visibility=visibility)
    TASK_REGISTRY.register(task_registration)
    return dataclass_class


def guess_root_task(*packages: str) -> Optional[TaskReference]:
    """
    Attempt to guess the root task by finding one with no references.

    The main point is to support the quick start use case, and is not
    intended for long-lived projects. It has the following caveats.

    CAVEAT 1: It produces a heuristic guess (not perfect).
    CAVEAT 2: It is quite inefficient for large numbers of tasks.

    Caveats aside, it prefers to fail, rather than return a bad root task.

    :param packages: top level package names
    :return: root task registration if found, None if not
    """
    candidates_by_class_id: Dict[int, TaskRegistration] = {}
    for class_id, registration in TASK_REGISTRY.by_class_id.items():
        if not registration.registered_class.__module__.startswith('jiig.'):
            candidates_by_class_id[class_id] = registration
    # Crude check for need to warn about possible performance issues.
    if len(candidates_by_class_id) > 20:
        log_warning('Larger projects should declare an explicit root task.')
    # Build and pare down a list of candidate registered tasks.
    for registration in TASK_REGISTRY.by_class_id.values():
        remove_class_ids: List[int] = []
        for reference in registration.tasks.values():
            # Class reference? Remove exact match from unreferenced.
            if isclass(reference) and issubclass(reference, RegisteredTask):
                for candidate_class_id, candidate in candidates_by_class_id.items():
                    if candidate.registered_class == reference:
                        remove_class_ids.append(candidate_class_id)
            # Module string or instance? Remove matching names from unreferenced.
            else:
                module_names: List[str] = []
                if isinstance(reference, str):
                    module_names.append(reference)
                    for package in packages:
                        module_names.append('.'.join([package, reference]))
                else:
                    module_names.append(reference.__name__)
                for candidate_class_id, candidate in candidates_by_class_id.items():
                    for module_name in module_names:
                        if candidate.registered_class.__module__ == module_name:
                            remove_class_ids.append(candidate_class_id)
                            break
        # Remove matches.
        for remove_class_id in remove_class_ids:
            del candidates_by_class_id[remove_class_id]
    if len(candidates_by_class_id) == 0:
        log_error('Root task not found.')
        return None
    if len(candidates_by_class_id) != 1:
        names = sorted([candidate.full_name for candidate in candidates_by_class_id.values()])
        log_error(f'More than one root task candidate.', *names)
        return None
    return list(candidates_by_class_id.values())[0].registered_class
