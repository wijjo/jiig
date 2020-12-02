from typing import Text

from jiig.registration import TaskFunction, Argument, Description, TaskFunctionsSpec
from jiig.utility.footnotes import NotesSpec, NoteDict

from .task_decorator import task


def sub_task(parent: TaskFunction,
             name: Text,
             *arguments: Argument,
             description: Description = None,
             notes: NotesSpec = None,
             dependencies: TaskFunctionsSpec = None,
             receive_trailing_arguments: bool = False,
             footnotes: NoteDict = None,
             hidden_task: bool = False,
             auxiliary_task: bool = False,
             **_unexpected_kwargs):
    """
    Decorator for declaring a sub-task function.

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
                auxiliary_task=auxiliary_task,
                **_unexpected_kwargs)
