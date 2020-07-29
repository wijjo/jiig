from __future__ import annotations
import os
import sys
from dataclasses import dataclass
from typing import Dict, Text, Optional, Callable, List

from . import task_runner


# === Runner factory

# Runner factory registered by @runner_factory decorator. Last registered one wins.
RunnerFactoryFunction = Callable[[task_runner.RunnerData], task_runner.TaskRunner]
RUNNER_FACTORY: Optional[RunnerFactoryFunction] = None


def create_runner(data: task_runner.RunnerData) -> task_runner.TaskRunner:
    if RUNNER_FACTORY:
        return RUNNER_FACTORY(data)
    return task_runner.TaskRunner(data)


# === Task registry

TaskFunction = Callable[[task_runner.TaskRunner], None]


@dataclass
class MappedTask:
    """
    Externally-visible task that gets mapped into the command line interface.

    NB: Do not create directly. It is done by the @task() decorator.
    """

    # noinspection PyShadowingBuiltins
    task_function: TaskFunction
    name: Optional[Text]
    parent: Optional[MappedTask]
    dest_name: Optional[Text]
    metavar: Optional[Text]
    help: Text
    options: Dict[Text, Dict]
    arguments: List[Dict]
    execution_tasks: List[MappedTask]
    # Sub-tasks added when discovered child tasks reference this as the parent.
    sub_tasks: List[MappedTask] = None

    @property
    def tag(self) -> Text:
        return self.name.upper() if self.name else None

    @property
    def folder(self) -> Text:
        # noinspection PyUnresolvedReferences
        return os.path.dirname(sys.modules[self.task_function.__module__].__file__)


MAPPED_TASKS: List[MappedTask] = []
MAPPED_TASKS_BY_ID: Dict[int, MappedTask] = {}
# To help map task name in command line arguments to MappedTask.
MAPPED_TASKS_BY_DEST_NAME: Dict[Text, MappedTask] = {}


# === Options

class ToolOptions:
    name = os.path.basename(sys.argv[0])
    description = '(no description provided)'


def options(name: Text = None,
            description: Text = None):
    if name is not None:
        ToolOptions.name = name
    if description is not None:
        ToolOptions.description = description
