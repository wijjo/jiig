"""
Task registry.
"""

import os
from dataclasses import dataclass, is_dataclass
from typing import Text, Dict, Type, get_type_hints, get_args, List, Union, TypeVar

from jiig.field import Field
from jiig.util.footnotes import NotesList, NotesDict

from ._registry import Registration, Registry

T_task = TypeVar('T_task')
TaskReference = Union[Type['RegisteredTask'], Text, object]

DEFAULT_TASK_DESCRIPTION = '(no description, e.g. in task doc string)'


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
    # Make sure there's a tasks dict, even if empty.
    if tasks is None:
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
    registered_task = TaskRegistration(handler_class=dataclass_class,
                                       description=description,
                                       notes=notes,
                                       footnotes=footnotes,
                                       tasks=tasks,
                                       fields=fields,
                                       visibility=visibility)
    TASK_REGISTRY.register(registered_task)
    return dataclass_class
