"""Data for a registered/mapped, task."""

import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Text, List

from jiig.internal import OptionList, ArgumentList, NotesList
from jiig.task_runner import TaskFunction
from jiig.utility.footnotes import FootnoteDict


@dataclass
class MappedTask:
    """
    Externally-visible task that gets mapped into the command line interface.

    NB: Do not create directly. It is done by the @task() decorator.
    """
    # noinspection PyShadowingBuiltins
    task_function: TaskFunction
    name: Text
    parent: Optional['MappedTask']
    dest_name: Text
    metavar: Text
    help: Text
    description: Text
    notes: NotesList
    options: OptionList
    arguments: ArgumentList
    footnotes: Optional[FootnoteDict]
    execution_tasks: List['MappedTask']
    help_visibility: int
    # True on the actual task that needs trailing arguments.
    trailing_arguments: bool = False
    # True on a root task that has a child that wants trailing arguments.
    need_trailing_arguments: bool = False
    # Sub-tasks added when discovered child tasks reference this as the parent.
    sub_tasks: List['MappedTask'] = field(default_factory=list)

    @property
    def folder(self) -> Text:
        """
        Get task module folder as property.

        :return: folder containing task module
        """
        # noinspection PyUnresolvedReferences
        return os.path.dirname(sys.modules[self.task_function.__module__].__file__)

    def get_full_command_names(self) -> List[Text]:
        """
        Get task/sub-task names in top to bottom order.

        :return: task/sub-task name list
        """
        names = [self.name]
        mapped_task = self
        while mapped_task.parent:
            names.insert(0, mapped_task.parent.name)
            mapped_task = mapped_task.parent
        return names
