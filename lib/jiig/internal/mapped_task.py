"""Data for a registered/mapped, task."""

import os
import sys
from dataclasses import dataclass
from typing import Optional, Text, List, Iterator

from jiig.internal import TaskFunction, OptionDict, ArgumentList


@dataclass
class MappedTask:
    """
    Externally-visible task that gets mapped into the command line interface.

    NB: Do not create directly. It is done by the @task() decorator.
    """

    # noinspection PyShadowingBuiltins
    task_function: TaskFunction
    name: Optional[Text]
    parent: Optional['MappedTask']
    dest_name: Optional[Text]
    metavar: Optional[Text]
    help: Text
    epilog: Optional[Text]
    options: OptionDict
    arguments: ArgumentList
    execution_tasks: List['MappedTask']
    # True on the actual task that needs trailing arguments.
    trailing_arguments: bool = False
    # True on a root task that has a child that wants trailing arguments.
    need_trailing_arguments: bool = False
    # True for a tool-management task the should normally not be visible.
    hidden_task: bool = False
    # True for a task, like help, that should be listed separate from tool tasks.
    auxiliary_task: bool = False
    # Sub-tasks added when discovered child tasks reference this as the parent.
    sub_tasks: List['MappedTask'] = None

    @property
    def tag(self) -> Text:
        return self.name.upper() if self.name else None

    @property
    def primary_task(self) -> bool:
        return not (self.auxiliary_task or self.hidden_task)

    @property
    def folder(self) -> Text:
        # noinspection PyUnresolvedReferences
        return os.path.dirname(sys.modules[self.task_function.__module__].__file__)

    def get_full_command_names(self) -> List[Text]:
        names = [self.name]
        mapped_task = self
        while mapped_task.parent:
            names.insert(0, mapped_task.parent.name)
            mapped_task = mapped_task.parent
        return names

    def sub_task_names(self) -> Iterator[Text]:
        if self.sub_tasks:
            for sub_task in self.sub_tasks:
                if sub_task.name:
                    yield sub_task.name
