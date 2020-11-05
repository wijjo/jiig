"""
Jiig task declaration support, including decorators.
"""

from inspect import isfunction
from typing import Text

from jiig.internal.registry import register_task
from jiig.external.typing import Description
from jiig.external.task_runner import TaskFunction, TaskFunctionsSpec
from jiig.utility.console import abort
from jiig.utility.footnotes import FootnoteDict, NotesSpec
from .argument import MappedArgument


def task(name: Text,
         *arguments: MappedArgument,
         description: Description = None,
         parent: TaskFunction = None,
         notes: NotesSpec = None,
         dependencies: TaskFunctionsSpec = None,
         receive_trailing_arguments: bool = False,
         footnotes: FootnoteDict = None,
         hidden_task: bool = False,
         auxiliary_task: bool = False):
    """
    Decorator for mapped task functions.

    All footnotes are displayed, even if not referenced in text by "[name]" at
    the end of a string. Unreferenced ones are displayed naked, without labels.
    In effect this allows the addition of general task notes.

    :param name: task name
    :param arguments: arguments and options classes and or instances
    :param description: task description
    :param parent: task function of parent task for sub-command
    :param notes: additional notes displayed after help body
    :param dependencies: task functions of dependency tasks
    :param receive_trailing_arguments: accept extra trailing arguments (valid for
                                       top level command)
    :param footnotes: labeled footnotes that can be referenced by task, option, or
                      argument help text (see note above about unreferenced ones)
    :param hidden_task: normally-hidden tool-management task if True
    :param auxiliary_task: used when commands like help should be listed separately
    """
    # Check for missing parentheses. Will not support that kind of decorator,
    # because any solution would have to accept, with no type checking, any and
    # all arguments in order to support both ways of using the decorator.
    if isfunction(name) and parent is None and dependencies is None:
        abort(f'@task decorator for function "{name.__name__}" must'
              f' have parentheses, even if empty')

    # Called after the outer function returns to provide the task function.
    def inner(task_function: TaskFunction) -> TaskFunction:
        register_task(task_function=task_function,
                      name=name,
                      parent=parent,
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


def sub_task(parent: TaskFunction,
             name: Text,
             *arguments: MappedArgument,
             description: Description = None,
             notes: NotesSpec = None,
             dependencies: TaskFunctionsSpec = None,
             receive_trailing_arguments: bool = False,
             footnotes: FootnoteDict = None,
             hidden_task: bool = False,
             auxiliary_task: bool = False):
    """
    Decorator for mapped sub-task functions.

    All footnotes are displayed, even if not referenced in text by "[name]" at
    the end of a string. Unreferenced ones are displayed naked, without labels.
    In effect this allows the addition of general task notes.

    :param parent: task function of parent task
    :param name: task name
    :param arguments: arguments and options classes and or instances
    :param description: task description
    :param notes: additional notes displayed after help body
    :param dependencies: task functions of dependency tasks
    :param receive_trailing_arguments: accept extra trailing arguments (valid for
                                       top level command)
    :param footnotes: labeled footnotes that can be referenced by task, option, or
                      argument help text (see note above about unreferenced ones)
    :param hidden_task: normally-hidden tool-management task if True
    :param auxiliary_task: used when commands like help should be listed separately
    """
    return task(name,
                *arguments,
                description=description,
                parent=parent,
                notes=notes,
                dependencies=dependencies,
                receive_trailing_arguments=receive_trailing_arguments,
                footnotes=footnotes,
                hidden_task=hidden_task,
                auxiliary_task=auxiliary_task)
