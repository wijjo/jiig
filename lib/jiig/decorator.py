"""
Jiig decorators.
"""

from inspect import isfunction
from typing import Callable, Text

from jiig.internal import TaskArgumentsSpecList, NotesRawData
from jiig.internal.registry import register_task, register_runner_factory
from jiig.task_runner import RunnerFactoryFunction, TaskFunction, TaskFunctionsSpec
from jiig.utility.console import abort
from jiig.utility.footnotes import FootnoteDict


def runner_factory() -> Callable[[RunnerFactoryFunction], RunnerFactoryFunction]:
    """Decorator for custom runner factories."""
    def inner(function: RunnerFactoryFunction) -> RunnerFactoryFunction:
        register_runner_factory(function)
        return function
    return inner


# noinspection PyShadowingBuiltins
def task(name: Text = None,
         parent: TaskFunction = None,
         help: Text = None,
         description: Text = None,
         notes: NotesRawData = None,
         arguments: TaskArgumentsSpecList = None,
         dependencies: TaskFunctionsSpec = None,
         receive_trailing_arguments: bool = False,
         footnotes: FootnoteDict = None,
         hidden_task: bool = False,
         auxiliary_task: bool = False):
    """
    Decorator for mapped task functions.

    Name is None for abstract tasks that are only used to pull in options,
    arguments, or initialization/validation logic in the task function.

    All footnotes are displayed, even if not referenced in text by "[name]" at
    the end of a string. Unreferenced ones are displayed naked, without labels.
    In effect this allows the addition of general task notes.

    :param name: task name or None to use default
    :param parent: task function of parent task for sub-command
    :param help: text displayed in help task lists
    :param description: text displayed below usage in help screen
    :param notes: additional notes displayed after help body
    :param arguments: positional arguments and or options list
    :param dependencies: task functions of dependency tasks
    :param receive_trailing_arguments: accept extra trailing arguments (valid for top level command)
    :param footnotes: labeled footnotes that can be referenced by task, option, or
                      argument help text (see note above about unreferenced ones)
    :param hidden_task: normally-hidden tool-management task if True
    :param auxiliary_task: used when commands like help should be listed separately
    """
    # Check for missing parentheses. Will not support that kind of decorator,
    # because any solution would have to accept, with no type checking, any and
    # all arguments in order to support both ways of using the decorator.
    if (isfunction(name)
            and parent is None
            and help is None
            and arguments is None
            and dependencies is None):
        abort(f'@task decorator for function "{name.__name__}" must'
              f' have parentheses, even if empty')

    # Called after the outer function returns to provide the task function.
    def inner(task_function: TaskFunction) -> TaskFunction:
        register_task(task_function=task_function,
                      name=name,
                      parent=parent,
                      help=help,
                      description=description,
                      notes=notes,
                      arguments=arguments,
                      dependencies=dependencies,
                      receive_trailing_arguments=receive_trailing_arguments,
                      footnotes=footnotes,
                      hidden_task=hidden_task,
                      auxiliary_task=auxiliary_task)
        return task_function

    return inner
