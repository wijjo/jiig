"""Jiig declaration decorators."""

import sys
from inspect import isfunction

from .registry import SubTaskCollection, TaskFunction, TASK_REGISTRY, TaskRegistrationRecord
from .util.log import abort


def task(naked_task_function: TaskFunction = None,
         /,
         tasks: SubTaskCollection = None,
         secondary: SubTaskCollection = None,
         hidden: SubTaskCollection = None,
         **driver_hints,
         ) -> TaskFunction:
    """
    Task function decorator.

    :param naked_task_function: not used explicitly, only non-None for naked @task functions
    :param tasks: optional sub-task reference(s) as sequence or dictionary
    :param secondary: optional secondary sub-task reference(s) as sequence or dictionary
    :param hidden: optional hidden sub-task reference(s) as sequence or dictionary
    """
    def _register(task_function: TaskFunction) -> TaskFunction:
        # noinspection PyUnresolvedReferences
        registered_task = TaskRegistrationRecord(
            implementation=task_function,
            module=sys.modules[task_function.__module__],
            primary_tasks=tasks,
            secondary_tasks=secondary,
            hidden_tasks=hidden,
            driver_hints=driver_hints,
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
