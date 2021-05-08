"""Task registry."""
import dataclasses
import os
import sys
from dataclasses import dataclass
from typing import Text, Dict, Type, get_type_hints, get_args

from jiig.util.footnotes import NotesList, NotesDict

from .field import Field
from .task_specification import TaskSpecification, TaskReference


class TaskRegistry:
    """Registered task specifications indexed by module and class ID."""
    by_module_id: Dict[int, TaskSpecification] = {}
    by_class_id: Dict[int, TaskSpecification] = {}


def register_task(cls: Type,
                  description: Text = None,
                  notes: NotesList = None,
                  footnotes: NotesDict = None,
                  tasks: Dict[Text, TaskReference] = None,
                  visibility: int = None,
                  ) -> Type:
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
    def _default_description():
        return cls.__doc__ and cls.__doc__.split(os.linesep)[0] or '(no task description)'
    # Wrap the class in a dataclass.
    if dataclasses.is_dataclass(cls):
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
    task_spec = TaskSpecification(handler_class=dataclass_class,
                                  description=description or _default_description(),
                                  notes=notes or [],
                                  footnotes=footnotes or {},
                                  tasks=tasks or {},
                                  fields=fields,
                                  visibility=visibility)
    TaskRegistry.by_module_id[id(sys.modules[cls.__module__])] = task_spec
    TaskRegistry.by_class_id[id(cls)] = task_spec
    return dataclass_class


# TODO: The decorator is obsolete, and should disappear completely.
# XXX def task(description_or_class: Union[Text, Type] = None,
# XXX          notes: NotesList = None,
# XXX          footnotes: NotesDict = None,
# XXX          tasks: Dict[Text, TaskReference] = None,
# XXX          visibility: int = 0,
# XXX          ) -> Callable:
# XXX     """
# XXX     Decorator for declaring task classes.
# XXX
# XXX     Supports use either as a naked decorator (not called) or by calling as a
# XXX     function with parameters.
# XXX
# XXX     If used naked, i.e. without being called, `description_or_class` will be a
# XXX     task handler class.
# XXX
# XXX     :param description_or_class: description (default: doc string) or task handler class
# XXX     :param notes: task help notes
# XXX     :param footnotes: named footnotes displayed in task help if referenced by "[<name>]"
# XXX     :param tasks: sub-task classes, modules, or module full name, by name
# XXX     :param visibility: 0=normal, 1=secondary, 2=hidden
# XXX     :return: inner function that receives the class
# XXX     """
# XXX     # Naked decorators should register immediately.
# XXX     if isclass(description_or_class):
# XXX         return register_task(description_or_class)
# XXX
# XXX     # Parameterized decorators wait for the inner call to register.
# XXX     def inner(cls: Type = None) -> Type:
# XXX         return register_task(cls,
# XXX                              description=description_or_class,
# XXX                              notes=notes,
# XXX                              footnotes=footnotes,
# XXX                              tasks=tasks,
# XXX                              visibility=visibility)
# XXX
# XXX     return inner
