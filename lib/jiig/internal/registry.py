"""Task and associated tool data registry."""

from __future__ import annotations
import os
import sys
from dataclasses import dataclass
from typing import Dict, Text, Optional, Callable, List, Iterator

from jiig import task_runner


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
    # This is True on the actual task that needs trailing arguments.
    trailing_arguments: bool = False
    # This is True on a root task that has a child that wants trailing arguments.
    need_trailing_arguments: bool = False
    # Sub-tasks added when discovered child tasks reference this as the parent.
    sub_tasks: List[MappedTask] = None

    @property
    def tag(self) -> Text:
        return self.name.upper() if self.name else None

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


MAPPED_TASKS: List[MappedTask] = []
# For quick lookups of parent and dependency tasks while processing @task decorator calls.
MAPPED_TASKS_BY_ID: Dict[int, MappedTask] = {}
# To help map task name in command line arguments to MappedTask by argparse destination names.
MAPPED_TASKS_BY_DEST_NAME: Dict[Text, MappedTask] = {}


def get_primary_task_names() -> Iterator[Text]:
    """Yield primary task names (unsorted)."""
    for mt in MAPPED_TASKS:
        if not mt.parent and mt.name:
            yield mt.name


# === Options

class ToolOptions:
    name = None
    description = None
    disable_alias = False
    disable_help = False
    disable_debug = False
    disable_dry_run = False
    disable_verbose = False


def options(name: Text = None,
            description: Text = None,
            disable_alias: bool = None,
            disable_help: bool = None,
            disable_debug: bool = None,
            disable_dry_run: bool = None,
            disable_verbose: bool = None):
    # Only set values for the keywords that were provided.
    if name is not None:
        ToolOptions.name = name
    if description is not None:
        ToolOptions.description = description
    if disable_alias is not None:
        ToolOptions.disable_alias = disable_alias
    if disable_help is not None:
        ToolOptions.disable_help = disable_help
    if disable_debug is not None:
        ToolOptions.disable_debug = disable_debug
    if disable_dry_run is not None:
        ToolOptions.disable_dry_run = disable_dry_run
    if disable_verbose is not None:
        ToolOptions.disable_verbose = disable_verbose
