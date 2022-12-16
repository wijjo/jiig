# Copyright (C) 2020-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""
Jiig declaration decorators.

Postpones importing task_registry and its dependencies until @task decorator is
invoked in order to keep this module's visible dependencies minimal. This allows
it to be imported from the jiig package root __init__.py without pulling in
extra dependencies.
"""

import sys
from inspect import isfunction

from .types import SubTaskCollection, TaskFunction
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
    :param driver_hints: driver hint dictionary
    :return: wrapper task function
    """
    if naked_task_function is None:
        return _task_decorator_called(tasks, secondary, hidden, driver_hints)
    return _task_decorator_naked(naked_task_function)


def _task_decorator_called(
        tasks: SubTaskCollection | None,
        secondary: SubTaskCollection | None,
        hidden: SubTaskCollection | None,
        driver_hints: dict,
) -> TaskFunction:
    """
    @task() decorator implementation when called with arguments.

    :param tasks: optional sub-task reference(s) as sequence or dictionary
    :param secondary: optional secondary sub-task reference(s) as sequence or dictionary
    :param hidden: optional hidden sub-task reference(s) as sequence or dictionary
    :param driver_hints: driver hint dictionary
    :return: wrapper task function
    """
    # Import internal dependency locally to avoid circular dependencies due to
    # tasks module referencing global symbols, like Field, Registry, etc..
    from .internal.registration.tasks import TASK_REGISTRY, TaskRegistrationRecord

    def _register(task_function: TaskFunction) -> TaskFunction:
        # task_function.__module__ may be None, e.g. for tasks in a Jiig script.
        # noinspection PyUnresolvedReferences
        registered_task = TaskRegistrationRecord(
            implementation=task_function,
            module=sys.modules.get(task_function.__module__),
            primary_tasks=tasks,
            secondary_tasks=secondary,
            hidden_tasks=hidden,
            driver_hints=driver_hints,
        )
        TASK_REGISTRY.register(registered_task)
        return task_function

    def _inner(function: TaskFunction) -> TaskFunction:
        return _register(function)

    return _inner


def _task_decorator_naked(
        naked_task_function: TaskFunction,
) -> TaskFunction:
    # @task decorator implementation when "naked", i.e. without parens/arguments.
    # Import internal dependency locally to avoid circular dependencies due to
    # tasks module referencing global symbols, like Field, Registry, etc..
    from .internal.registration.tasks import TASK_REGISTRY, TaskRegistrationRecord
    if (not isfunction(naked_task_function)
            or TASK_REGISTRY.is_registered(naked_task_function)):
        abort(f'Unexpected positional argument for @task decorator.', naked_task_function)
    # noinspection PyUnresolvedReferences
    registered_task = TaskRegistrationRecord(
        implementation=naked_task_function,
        module=sys.modules.get(naked_task_function.__module__),
        primary_tasks=None,
        secondary_tasks=None,
        hidden_tasks=None,
        driver_hints=None,
    )
    TASK_REGISTRY.register(registered_task)
    return naked_task_function
