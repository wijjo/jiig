"""
Jiig decorators.
"""

from typing import Callable, Text, Dict, Union, Sequence, List, Set

from . import registry, utility


def runner_factory() -> Callable[[registry.RunnerFactoryFunction], registry.RunnerFactoryFunction]:
    """Decorator for custom runner factories."""
    def inner(function: registry.RunnerFactoryFunction) -> registry.RunnerFactoryFunction:
        registry.RUNNER_FACTORY = function
        return function
    return inner


# noinspection PyShadowingBuiltins
def task(name: Text = None,
         parent: registry.TaskFunction = None,
         help: Text = None,
         options: Dict[Union[Text, Sequence[Text]], Dict] = None,
         arguments: List[Dict] = None,
         dependencies: List[registry.TaskFunction] = None):
    """
    Decorator for mapped task functions.

    Name is None for abstract tasks that are only used to pull in options,
    arguments, or initialization/validation logic in the task function.

    Only named mapped tasks are added to an argument sub-parser.
    """
    if parent:
        parent_mapped_task = registry.MAPPED_TASKS_BY_ID.get(id(parent))
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
        dest_name = utility.make_dest_name(*names)
        metavar = utility.make_metavar(*names)
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
    merged_execution_tasks: List[registry.MappedTask] = []
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
            dependency_mapped_task = registry.MAPPED_TASKS_BY_ID.get(dependency_function_id, None)
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
    def inner(task_function: registry.TaskFunction) -> registry.TaskFunction:
        mt = registry.MappedTask(task_function=task_function,
                                 name=name,
                                 parent=parent_mapped_task,
                                 dest_name=dest_name,
                                 metavar=metavar,
                                 help=help,
                                 options=merged_options,
                                 arguments=merged_arguments,
                                 execution_tasks=merged_execution_tasks)
        # Complete the registration, now that there is a new MappedTask.
        registry.MAPPED_TASKS_BY_ID[id(task_function)] = mt
        if dest_name:
            registry.MAPPED_TASKS_BY_DEST_NAME[dest_name] = mt
        # Add to sub_tasks list of parent, if there is a parent.
        if parent_mapped_task:
            if parent_mapped_task.sub_tasks is None:
                parent_mapped_task.sub_tasks = []
            parent_mapped_task.sub_tasks.append(mt)
        else:
            registry.MAPPED_TASKS.append(mt)
        return task_function
    return inner