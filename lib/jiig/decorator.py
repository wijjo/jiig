"""
Jiig decorators.
"""

from inspect import isfunction
from typing import Callable, Text, Dict, Union, Sequence, List, Set, Tuple, Optional

from jiig.internal import registry
from jiig.utility.cli import make_dest_name, make_metavar
from jiig.utility.console import abort, log_error


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
         epilog: Text = None,
         options: Dict[Union[Text, Sequence[Text]], Dict] = None,
         arguments: List[Dict] = None,
         dependencies: List[registry.TaskFunction] = None,
         trailing_arguments: bool = False,
         common_options: Sequence[Text] = None,
         common_arguments: Sequence[Text] = None):
    """
    Decorator for mapped task functions.

    Name is None for abstract tasks that are only used to pull in options,
    arguments, or initialization/validation logic in the task function.

    :param name: task name or None to use default
    :param parent: task function of parent task for sub-command
    :param help: help string
    :param epilog: additional help text displayed after the help body
    :param options: flag options as dictionary mapping option flags or flag tuples
                    to add_argument() parameter dictionaries
    :param arguments: positional arguments as list of add_argument() parameter dicts
    :param dependencies: task functions of dependency tasks
    :param trailing_arguments: pass along trailing extra arguments (only valid for
                               primary top level command)
    :param common_options: common options that may be shared between tasks
    :param common_arguments: common arguments that may be shared between tasks
    """

    # Check for missing parentheses. Will not support that kind of decorator,
    # because any solution would have to accept, with no type checking, any and
    # all arguments in order to support both ways of using the decorator.
    if (isfunction(name)
            and parent is None
            and help is None
            and options is None
            and arguments is None
            and dependencies is None):
        abort(f'@task decorator for function "{name.__name__}" must'
              f' have parentheses, even if empty')

    # Split a common option/argument specifier into dest name and optional
    # `nargs` specifier.
    def split_spec(spec: Text) -> Tuple[Text, Optional[Text]]:
        if spec[-1] in ('?', '*', '+'):
            return spec[:-1], spec[-1]
        return spec, None

    if common_options:
        all_options = dict(options) if options else {}
        for option_spec in common_options:
            dest, nargs = split_spec(option_spec)
            key = registry.ToolOptions.common_option_key_by_dest.get(dest)
            if key is not None:
                if nargs is None:
                    all_options[key] = registry.ToolOptions.common_options[key]
                else:
                    all_options[key] = dict(registry.ToolOptions.common_options[key],
                                            nargs=nargs)
            else:
                log_error(f'Ignoring unknown Tzar standard option "{dest}".')
    else:
        all_options = options

    if common_arguments:
        all_arguments = list(arguments) if arguments else []
        for argument_spec in common_arguments:
            dest, nargs = split_spec(argument_spec)
            key = registry.ToolOptions.common_option_key_by_dest.get(dest)
            if key is not None:
                if nargs is None:
                    all_arguments.append(
                        registry.ToolOptions.common_options[key])
                else:
                    all_arguments.append(
                        dict(registry.ToolOptions.common_options[key],
                             nargs=nargs))
            else:
                log_error(f'Ignoring unknown Tzar standard argument "{dest}".')
    else:
        all_arguments = arguments

    # Called after the outer function returns to provide the task function.
    def inner(task_function: registry.TaskFunction) -> registry.TaskFunction:

        if parent:
            parent_mapped_task = registry.MAPPED_TASKS_BY_ID.get(id(parent))
            if not parent_mapped_task:
                abort(f'Unmapped parent task: {parent.__name__}')
            if not parent_mapped_task.name:
                abort(f'Parent task {parent_mapped_task.__class__.__name__}'
                      f' does not have a name')
        else:
            parent_mapped_task = None

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
        _merge_opts_and_args(all_options, all_arguments)

        # Settle on the final task name. Fall back to function name.
        task_name = name
        if not task_name and not task_function.__name__.startswith('_'):
            task_name = task_function.__name__

        # Generate argument parser `dest` and `metavar` names.
        if task_name:
            names = []
            ancestor_mapped_task = parent_mapped_task
            while ancestor_mapped_task:
                names.append(ancestor_mapped_task.name.upper())
                ancestor_mapped_task = ancestor_mapped_task.parent
            names.append(task_name.upper())
            dest_name = make_dest_name(*names)
            metavar = make_metavar(*names)
        else:
            dest_name = None
            metavar = None

        # Settle on the final help string. Fall back to first line of function doc string.
        task_help = help
        if not task_help:
            if task_function.__doc__:
                doc_string = task_function.__doc__.strip()
                if doc_string:
                    task_help = doc_string.splitlines()[0]
        if not task_help:
            task_help = '(no help in @task decorator or doc string)'

        # The root task needs to flag if it or any child wants trailing arguments.
        need_trailing_arguments = False
        if trailing_arguments:
            if parent_mapped_task:
                while True:
                    if not parent_mapped_task.parent:
                        parent_mapped_task.need_trailing_arguments = True
                        break
                    parent_mapped_task = parent_mapped_task.parent
            else:
                need_trailing_arguments = True

        # Create the registered MappedTask object.
        mt = registry.MappedTask(task_function=task_function,
                                 name=task_name,
                                 parent=parent_mapped_task,
                                 dest_name=dest_name,
                                 metavar=metavar,
                                 help=task_help,
                                 epilog=epilog,
                                 options=merged_options,
                                 arguments=merged_arguments,
                                 trailing_arguments=trailing_arguments,
                                 need_trailing_arguments=need_trailing_arguments,
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
