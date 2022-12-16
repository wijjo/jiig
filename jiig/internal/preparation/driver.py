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
Driver factory.
"""

from dataclasses import dataclass
from typing import Self

from jiig.constants import TOP_TASK_LABEL, SUB_TASK_LABEL, TOP_TASK_DEST_NAME
from jiig.driver import DriverInitializationData
from jiig.driver.driver import Driver, DriverOptions
from jiig.util.options import OPTIONS
from jiig.util.log import set_log_writer, log_message

from jiig.internal.configuration.tool import ToolConfiguration


@dataclass
class PreparedDriver:

    driver: Driver
    initialization_data: DriverInitializationData

    @classmethod
    def prepare(cls,
                tool_config: ToolConfiguration,
                driver_args: list[str],
                ) -> Self:
        """
        Prepare configured driver.

        :param tool_config: tool configuration with driver registration, options, and metadata
        :param driver_args: driver arguments
        :return: prepared driver
        """
        supported_global_options: list[str] = []
        if not tool_config.options.disable_debug:
            supported_global_options.append('debug')
        if not tool_config.options.disable_dry_run:
            supported_global_options.append('dry_run')
        if not tool_config.options.disable_verbose:
            supported_global_options.append('verbose')
        if tool_config.options.enable_pause:
            supported_global_options.append('pause')
        if tool_config.options.enable_keep_files:
            supported_global_options.append('keep_files')
        driver_options = DriverOptions(
            variant=tool_config.driver_variant,
            raise_exceptions=True,
            top_task_label=TOP_TASK_LABEL,
            sub_task_label=SUB_TASK_LABEL,
            top_task_dest_name=TOP_TASK_DEST_NAME,
            supported_global_options=supported_global_options,
        )
        driver: Driver = tool_config.driver_registration.implementation(
            tool_config.meta.tool_name,
            tool_config.meta.description,
            tool_config.paths,
            options=driver_options,
        )

        # Install the driver's log writer.
        set_log_writer(driver.get_log_writer())

        # Initialize the driver. Only display message once.
        initialization_data = driver.initialize_driver(driver_args)
        if not initialization_data.final_arguments:
            initialization_data.final_arguments = ['help']
        if not tool_config.venv_active:
            log_message('Jiig driver initialized.', debug=True)

        # Initialize option settings, which are shared through the util library.
        OPTIONS.from_strings(driver.enabled_global_options)

        return cls(driver, initialization_data)
