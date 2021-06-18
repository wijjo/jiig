"""Task registry."""

import dataclasses
import os
import sys
from dataclasses import dataclass
from typing import Text, Dict, Type, get_type_hints, get_args, List

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
            description = '(no task description)'
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
                                  description=description,
                                  notes=notes,
                                  footnotes=footnotes,
                                  tasks=tasks,
                                  fields=fields,
                                  visibility=visibility)
    TaskRegistry.by_module_id[id(sys.modules[cls.__module__])] = task_spec
    TaskRegistry.by_class_id[id(cls)] = task_spec
    return dataclass_class
