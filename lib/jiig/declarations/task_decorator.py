from inspect import isfunction
from typing import Text

from jiig.registration import register_task, Argument, Description, TaskFunction, \
    TaskFunctionsSpec
from jiig.utility.console import abort
from jiig.utility.footnotes import NotesSpec, NoteDict
from jiig.utility.general import plural


def task(name: Text,
         *arguments: Argument,
         description: Description = None,
         parent: TaskFunction = None,
         notes: NotesSpec = None,
         dependencies: TaskFunctionsSpec = None,
         receive_trailing_arguments: bool = False,
         footnotes: NoteDict = None,
         hidden_task: bool = False,
         auxiliary_task: bool = False,
         **_unexpected_kwargs):
    """
    Decorator for declaring a task function.

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
        abort(f'@task("{name}" ...) must have parentheses, even if empty')

    # Receiving **_unexpected_kwargs helps build a more informative error message.
    if _unexpected_kwargs:
        abort(f'@task("{name}" ...) received unexpected keyword'
              f' {plural("argument", _unexpected_kwargs)}:',
              ' '.join(_unexpected_kwargs.keys()))

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
