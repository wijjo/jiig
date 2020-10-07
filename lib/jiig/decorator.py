"""
Jiig decorators.
"""

from inspect import isfunction
from typing import Callable, Text, Sequence, List

from jiig.internal import registry
from jiig.utility.console import abort


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
         options: registry.OptionRawDict = None,
         arguments: registry.ArgumentList = None,
         dependencies: List[registry.TaskFunction] = None,
         trailing_arguments: bool = False,
         common_options: Sequence[Text] = None,
         common_arguments: Sequence[Text] = None,
         hidden_task: bool = False,
         auxiliary_task: bool = False):
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
    :param hidden_task: normally-hidden tool-management task if True
    :param auxiliary_task: used when commands like help should be listed separately
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

    # Called after the outer function returns to provide the task function.
    def inner(task_function: registry.TaskFunction) -> registry.TaskFunction:
        registry.register_task(task_function=task_function,
                               name=name,
                               parent=parent,
                               help=help,
                               epilog=epilog,
                               options=options,
                               arguments=arguments,
                               dependencies=dependencies,
                               trailing_arguments=trailing_arguments,
                               common_options=common_options,
                               common_arguments=common_arguments,
                               hidden_task=hidden_task,
                               auxiliary_task=auxiliary_task)
        return task_function

    return inner
