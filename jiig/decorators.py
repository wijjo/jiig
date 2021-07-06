"""Jiig declaration decorators."""

import sys
from inspect import isfunction
from typing import Text, Sequence

from .registry import TaskReference, TaskFunction, TASK_REGISTRY, TaskRegistrationRecord
from .util.footnotes import NotesList, NotesDict
from .util.log import abort


def task(naked_task_function: TaskFunction = None,
         /,
         description: Text = None,
         notes: NotesList = None,
         footnotes: NotesDict = None,
         tasks: Sequence[TaskReference] = None,
         ) -> TaskFunction:
    """
    Task function decorator.

    :param naked_task_function: not used explicitly, only non-None for naked @task functions
    :param description: optional sub-task description
    :param notes: optional task notes list
    :param footnotes: optional task footnotes dictionary
    :param tasks: optional sub-task reference(s) as sequence or dictionary
    """
    def _register(task_function: TaskFunction) -> TaskFunction:
        # noinspection PyUnresolvedReferences
        registered_task = TaskRegistrationRecord(
            implementation=task_function,
            module=sys.modules[task_function.__module__],
            description=description,
            notes=notes,
            footnotes=footnotes,
            sub_task_references=tasks,
        )
        TASK_REGISTRY.register(registered_task)
        return task_function

    if naked_task_function is not None:
        if (not isfunction(naked_task_function)
                or TASK_REGISTRY.is_registered(naked_task_function)):
            abort(f'Unexpected positional argument for @task decorator.', naked_task_function)
        return _register(naked_task_function)

    def _inner(function: TaskFunction) -> TaskFunction:
        return _register(function)

    return _inner
