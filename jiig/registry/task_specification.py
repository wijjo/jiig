"""
Task specification that eventually feeds into a runtime task object.
"""

from dataclasses import dataclass
from typing import Type, Text, Dict, Union

from jiig.util.footnotes import NotesList, NotesDict

from .field import Field

# Reference to registered Task class, module name, or loaded module, with
# `object` representing loaded module, due to lack of better alternative.
TaskReference = Union[Type, Text, object]


@dataclass
class TaskSpecification:
    """
    Registered task specification.

    Not user-created. Constructed for registered Task classes.
    """

    handler_class: Type
    """Task handler class to be constructed with appropriate field data."""

    description: Text
    """Task description."""

    notes: NotesList
    """Task help notes."""

    footnotes: NotesDict
    """Named footnotes displayed in task help if referenced by "[<name>]"."""

    tasks: Dict[Text, TaskReference]
    """Sub-task references by name."""

    fields: Dict[Text, Field]
    """Argument/option definition dictionary."""

    visibility: int
    """Visibility, e.g. in help, with 0=normal, 1=secondary, 2=hidden."""
