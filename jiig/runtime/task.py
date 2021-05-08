"""
Task handler base class.
"""

from typing import Text, Dict

from jiig.registry import register_task, TaskReference
from jiig.util.footnotes import NotesList, NotesDict

from .runtime import Runtime


class Task:
    """
    Base Task call-back class.

    Use as a base for registered task classes. It provides type-checked method
    overrides and automatic class registration and wrapping as a dataclass.

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
        super().__init_subclass__(**kwargs)
        register_task(cls,
                      description=description,
                      notes=notes,
                      footnotes=footnotes,
                      tasks=tasks,
                      visibility=visibility)

    def on_run(self, runtime: Runtime):
        """
        Override-able method that gets called to run task logic.

        :param runtime: runtime data and API
        """
        pass

    def on_done(self, runtime: Runtime):
        """
        Override-able method called after running tasks in reverse order.

        :param runtime: runtime data and API
        """
        pass
