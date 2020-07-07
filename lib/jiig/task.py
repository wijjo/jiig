from __future__ import annotations
import sys
import os
from dataclasses import dataclass
from typing import Optional, List, Text, Dict, Callable, Set

from .runner import TaskRunner
from .utility import make_dest_name, make_metavar


TaskFunction = Callable[[TaskRunner], None]

MAPPED_TASKS: List[MappedTask] = []
MAPPED_TASKS_BY_ID: Dict[int, MappedTask] = {}
# To help map task name in command line arguments to MappedTask.
MAPPED_TASKS_BY_DEST_NAME: Dict[Text, MappedTask] = {}


@dataclass
class MappedTask:
    """
    Externally-visible task that gets mapped into the command line interface.

    NB: Do not create directly. It is done by the @map_task() decorator.
    """

    # noinspection PyShadowingBuiltins
    task_function: TaskFunction
    name: Optional[Text]
    parent: Optional[MappedTask]
    dest_name: Optional[Text]
    metavar: Optional[Text]
    description: Text
    help: Text
    options: Dict[Text, Dict]
    arguments: List[Dict]
    execution_tasks: List[MappedTask]
    not_inherited: bool
    # Sub-tasks added when discovered child tasks reference this as the parent.
    sub_tasks: List[MappedTask] = None

    @property
    def tag(self) -> Text:
        return self.name.upper() if self.name else None

    @property
    def folder(self) -> Text:
        # noinspection PyUnresolvedReferences
        return os.path.dirname(sys.modules[self.task_function.__module__].__file__)


# noinspection PyShadowingBuiltins
def map_task(name: Text = None,
             parent: TaskFunction = None,
             help: Text = None,
             description: Text = None,
             options: Dict[Text, Dict] = None,
             arguments: List[Dict] = None,
             dependencies: List[TaskFunction] = None,
             not_inherited: bool = False):
    """
    Decorator for mapped task functions.

    Name is None for abstract tasks that are only used to pull in options,
    arguments, or initialization/validation logic in the task function.

    Only named mapped tasks are added to an argument sub-parser.
    """
    if parent:
        parent_mapped_task = MAPPED_TASKS_BY_ID.get(id(parent))
        if not parent_mapped_task:
            raise RuntimeError(f'Unmapped parent task: {parent.__name__}')
        if not parent_mapped_task.name:
            raise RuntimeError(f'Parent task {parent_mapped_task.__class__.__name__}'
                               f' does not have a name')
    else:
        parent_mapped_task = None

    # Generate argument parser `dest` and `metavar` names.
    if name:
        names = []
        ancestor_mapped_task = parent_mapped_task
        while ancestor_mapped_task:
            names.append(ancestor_mapped_task.name.upper())
            ancestor_mapped_task = ancestor_mapped_task.parent
        names.append(name.upper())
        dest_name = make_dest_name(*names)
        metavar = make_metavar(*names)
    else:
        dest_name = None
        metavar = None

    # Perform roll-up to merge in data from parents and dependencies.
    #
    # Note that recursion is unnecessary. Parent and dependencies reference
    # actual functions, guaranteeing that the corresponding tasks were
    # previously rolled up and registered.
    #
    # The results:
    #  - The final execution task list includes (in order) each unique item from
    #    the parent execution task list, the parent task, and for each
    #    dependency, its execution task list, followed by that task.
    #  - The final options dictionary merges all dependency option dictionaries
    #    with the current task's.
    #  - The final argument list includes (in order) all dependency argument
    #    lists, followed by the current task's.
    merged_execution_tasks: List[MappedTask] = []
    # Catch and ignore tasks that are seen more than once via execution task lists.
    unique_function_ids: Set[int] = set()
    # The parent provides the execution task list for itself and its parents.
    if parent_mapped_task:
        if parent_mapped_task.execution_tasks:
            for parent_execution_task in parent_mapped_task.execution_tasks:
                merged_execution_tasks.append(parent_execution_task)
                unique_function_ids.add(id(parent_execution_task.task_function))
        merged_execution_tasks.append(parent_mapped_task)
        unique_function_ids.add(id(parent_mapped_task.task_function))
    # Merge unique execution tasks from dependencies.
    if dependencies:
        for dependency_function in dependencies:
            dependency_function_id = id(dependency_function)
            if dependency_function_id in unique_function_ids:
                continue
            dependency_mapped_task = MAPPED_TASKS_BY_ID.get(dependency_function_id, None)
            if not dependency_mapped_task:
                continue
            # Execution tasks property yields child tasks and the parent task.
            for dependency_execution_task in dependency_mapped_task.execution_tasks:
                dependency_execution_function_id = id(dependency_execution_task.task_function)
                if dependency_execution_function_id in unique_function_ids:
                    continue
                merged_execution_tasks.append(dependency_execution_task)
                unique_function_ids.add(dependency_execution_function_id)
            merged_execution_tasks.append(dependency_mapped_task)
            unique_function_ids.add(dependency_function_id)
    # Merge options and arguments from execution tasks. Enforce uniqueness by
    # only accepting the first instance of a particular dest name wins. So
    # higher level tasks lose to dependencies if they reuse dest names.
    merged_options: Dict[Text, Dict] = {}
    merged_arguments: List[Dict] = []
    unique_dest_names: Set[Text] = set()

    def _merge_opts_and_args(opts: Dict[Text, Dict], args: List[Dict]):
        if opts:
            for opt_flag, opt_data in opts.items():
                opt_dest_name = opt_data.get('dest', None)
                if opt_dest_name:
                    if opt_dest_name not in unique_dest_names:
                        merged_options[opt_flag] = opt_data
                        unique_dest_names.add(opt_dest_name)
        if args:
            for arg_data in args:
                arg_dest_name = arg_data.get('dest', None)
                if arg_dest_name:
                    if arg_dest_name not in unique_dest_names:
                        merged_arguments.append(arg_data)
                        unique_dest_names.add(arg_dest_name)
    for execution_task in merged_execution_tasks:
        _merge_opts_and_args(execution_task.options, execution_task.arguments)
    _merge_opts_and_args(options, arguments)

    # Called after the outer function returns to provide the task function.
    def inner(task_function: TaskFunction) -> TaskFunction:
        mt = MappedTask(task_function=task_function,
                        name=name,
                        parent=parent_mapped_task,
                        dest_name=dest_name,
                        metavar=metavar,
                        description=description,
                        help=help,
                        options=merged_options,
                        arguments=merged_arguments,
                        execution_tasks=merged_execution_tasks,
                        not_inherited=not_inherited)
        # Complete the registration, now that there is a new MappedTask.
        MAPPED_TASKS_BY_ID[id(task_function)] = mt
        if dest_name:
            MAPPED_TASKS_BY_DEST_NAME[dest_name] = mt
        # Add to sub_tasks list of parent, if there is a parent.
        if parent_mapped_task:
            if parent_mapped_task.sub_tasks is None:
                parent_mapped_task.sub_tasks = []
            parent_mapped_task.sub_tasks.append(mt)
        else:
            MAPPED_TASKS.append(mt)
        return task_function
    return inner
