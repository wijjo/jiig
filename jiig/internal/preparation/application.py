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
from typing import Self

from jiig.driver import DriverApplicationData
from jiig.driver.driver_task import DriverTask
from jiig.util.log import log_message, log_error
from jiig.util.text.grammar import pluralize

from ..registration.hints import HINT_REGISTRY
from ..registration.tasks import TaskField, AssignedTask

from .driver import PreparedDriver
from jiig.internal.configuration.tool import ToolConfiguration


def _populate_driver_task(driver_task: DriverTask,
                          fields: list[TaskField],
                          sub_tasks: list[AssignedTask],
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
                                                   sub_task.description,
                                                   sub_task.notes,
                                                   sub_task.footnotes,
                                                   sub_task.visibility,
                                                   sub_task.hints)
        _populate_driver_task(driver_sub_task, sub_task.fields, sub_task.sub_tasks)


@dataclass
class PreparedApplication:
    driver_app_data: DriverApplicationData
    driver_root_task: DriverTask
    task_stack: list[AssignedTask]

    @classmethod
    def prepare(cls,
                tool_config: ToolConfiguration,
                prepared_driver: PreparedDriver,
                ) -> Self:

        # Convert the runtime task hierarchy to a driver task hierarchy.
        driver_root_task = DriverTask(
            name=tool_config.meta.tool_name,
            description=tool_config.assigned_root_task.description,
            sub_tasks=[],
            fields=[],
            notes=tool_config.assigned_root_task.notes,
            footnotes=tool_config.assigned_root_task.footnotes,
            visibility=0,
            hints=tool_config.assigned_root_task.hints,
        )
        _populate_driver_task(driver_root_task,
                              tool_config.assigned_root_task.fields,
                              tool_config.assigned_root_task.sub_tasks)

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
        task_stack: list[AssignedTask] = [tool_config.assigned_root_task]
        for driver_task in driver_app_data.task_stack:
            for sub_task in task_stack[-1].sub_tasks:
                if sub_task.name == driver_task.name:
                    task_stack.append(sub_task)
                    break

        return cls(driver_app_data, driver_root_task, task_stack)
