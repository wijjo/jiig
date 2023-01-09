# Copyright (C) 2021-2022, Steven Cooper
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

"""Application/tasks preparation."""

from dataclasses import dataclass
from inspect import ismodule
from typing import Self, Iterator

from jiig.internal.configuration.tool import ToolConfiguration
from jiig.driver import DriverApplicationData
from jiig.driver.driver_task import DriverTask
from jiig.task import TASKS_BY_FUNCTION_ID, RegisteredTask, HINT_REGISTRY
from jiig.types import TaskFunction, TaskReference
from jiig.util.log import log_message, log_error, log_warning, abort
from jiig.util.text.grammar import pluralize

from ..task import RuntimeTask, TaskField

from .driver import PreparedDriver


def _populate_driver_task(driver_task: DriverTask,
                          fields: list[TaskField],
                          sub_tasks: list[RuntimeTask],
                          ):
    for task_field in fields:
        driver_task.add_field(name=task_field.name,
                              description=task_field.description,
                              element_type=task_field.element_type,
                              default=task_field.default,
                              repeat=task_field.repeat,
                              choices=task_field.choices)
    for sub_task in sub_tasks:
        driver_sub_task = driver_task.add_sub_task(sub_task.name,
                                                   sub_task.full_name,
                                                   sub_task.description,
                                                   sub_task.notes,
                                                   sub_task.footnotes,
                                                   sub_task.visibility,
                                                   sub_task.driver_hints)
        _populate_driver_task(driver_sub_task, sub_task.fields, sub_task.sub_tasks)


@dataclass
class PreparedApplication:
    driver_app_data: DriverApplicationData
    driver_root_task: DriverTask
    task_stack: list[RuntimeTask]

    @classmethod
    def prepare(cls,
                tool_config: ToolConfiguration,
                prepared_driver: PreparedDriver,
                ) -> Self:

        root_task_function = tool_config.root_task
        if root_task_function is None:
            root_task_function = guess_root_task_function(tool_config.meta.tool_name)
            if root_task_function is None:
                abort('Root task could not be guessed.')

        root_task = RuntimeTask.resolve(root_task_function, '(root)', 2, required=True)

        # Add built-in tasks.
        visibility = 2 if tool_config.options.hide_builtin_tasks else 1
        root_task_names = set(
            (sub_task.name for sub_task in root_task.sub_tasks))

        def _add_if_needed(name: str, task_ref: str):
            if not root_task_names.intersection({name, f'{name}[s]', f'{name}[h]'}):
                resolved_task = RuntimeTask.resolve(task_ref, name, visibility)
                if resolved_task is not None:
                    root_task.sub_tasks.append(resolved_task)

        if not tool_config.options.disable_help:
            _add_if_needed('help', 'jiig.tasks.help')
        if not tool_config.options.disable_alias:
            _add_if_needed('alias', 'jiig.tasks.alias')
        if tool_config.venv_required:
            _add_if_needed('venv', 'jiig.tasks.venv')

        # Convert the runtime task hierarchy to a driver task hierarchy.
        driver_root_task = DriverTask(
            name=tool_config.meta.tool_name,
            full_name=root_task.full_name,
            description=root_task.description,
            sub_tasks=[],
            fields=[],
            notes=root_task.notes,
            footnotes=root_task.footnotes,
            visibility=0,
            hints=root_task.driver_hints,
        )
        _populate_driver_task(driver_root_task,
                              root_task.fields,
                              root_task.sub_tasks)

        driver_app_data = prepared_driver.driver.initialize_application(
            prepared_driver.initialization_data, driver_root_task)
        log_message('Application initialized.', debug=True)

        # Check task hint usage.
        if prepared_driver.driver.supported_task_hints:
            HINT_REGISTRY.add_supported_task_hints(
                *prepared_driver.driver.supported_task_hints)
        bad_task_hints = HINT_REGISTRY.get_bad_task_hints()
        if bad_task_hints:
            log_error(f'Bad task {pluralize("hint", bad_task_hints)}:',
                      *bad_task_hints)

        # Check field hint usage.
        HINT_REGISTRY.add_supported_field_hints('repeat', 'choices', 'default')
        if prepared_driver.driver.supported_field_hints:
            HINT_REGISTRY.add_supported_field_hints(
                *prepared_driver.driver.supported_field_hints)
        bad_field_hints = HINT_REGISTRY.get_bad_field_hints()
        if bad_field_hints:
            log_error(f'Bad field {pluralize("hint", bad_field_hints)}:',
                      *bad_field_hints)

        # Convert driver task stack to RegisteredTask stack.
        task_stack: list[RuntimeTask] = [root_task]
        for driver_task in driver_app_data.task_stack:
            for sub_task in task_stack[-1].sub_tasks:
                if sub_task.name == driver_task.name:
                    task_stack.append(sub_task)
                    break

        return cls(driver_app_data, driver_root_task, task_stack)


def guess_root_task_function(*additional_packages: str) -> TaskFunction:
    """
    Attempt to guess the root task by finding one with no references.

    The main point is to support the quick start use case, and is not
    intended for long-lived projects. It has the following caveats.

    CAVEAT 1: It produces a heuristic guess (not perfect).
    CAVEAT 2: It is quite inefficient, O(N^2), for large numbers of tasks.
    CAVEAT 3: It only works with registered tasks, and won't find non-loaded ones.

    Caveats aside, it prefers to fail, rather than return a bad root task.

    :param additional_packages: additional package names for resolving named modules
    :return: root task implementation if found, None if not
    """
    # Gather the full initial candidate pool.
    candidates_by_id: dict[int, RegisteredTask] = {}
    candidate_ids_by_module_name: dict[str, int] = {}
    for item_id, registered_task in TASKS_BY_FUNCTION_ID.items():
        if (registered_task.module
                and not registered_task.module.__name__.startswith('jiig.')):
            candidates_by_id[item_id] = registered_task
            candidate_ids_by_module_name[registered_task.module.__name__] = item_id
    if len(candidates_by_id) > 20:
        log_warning('Larger projects should declare an explicit root task.')
    # Reduce candidate pool by looking for references to candidates.
    for registered_task in TASKS_BY_FUNCTION_ID.values():
        # Remove any candidates that are referenced. Handle module
        # instances, module strings, and function references.
        for reference in _iterate_tasks(registered_task):
            # Module name?
            if isinstance(reference, str):
                reference_id = candidate_ids_by_module_name.get(reference)
                if reference_id is None:
                    for package in additional_packages:
                        module_name = '.'.join([package, reference])
                        reference_id = candidate_ids_by_module_name.get(module_name)
                        if reference_id is not None:
                            break
            # Module instance?
            elif ismodule(reference):
                reference_id = candidate_ids_by_module_name.get(reference.__name__)
            # @task function?
            else:
                reference_id = id(reference)
            if reference_id is not None and reference_id in candidates_by_id:
                del candidates_by_id[reference_id]
    # Wrap-up.
    if len(candidates_by_id) == 0:
        abort('Root task not found.')
    if len(candidates_by_id) != 1:
        names = sorted([candidate.full_name for candidate in candidates_by_id.values()])
        abort(f'More than one root task candidate. {names}')
    return list(candidates_by_id.values())[0].task_function


def _iterate_tasks(registered_task: RegisteredTask) -> Iterator[TaskReference]:
    if registered_task.primary_tasks:
        for task_reference in registered_task.primary_tasks.values():
            yield task_reference
    if registered_task.secondary_tasks:
        for task_reference in registered_task.secondary_tasks.values():
            yield task_reference
    if registered_task.hidden_tasks:
        for task_reference in registered_task.hidden_tasks.values():
            yield task_reference
