# Copyright (C) 2020-2023, Steven Cooper
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

"""Driver factory."""

from types import ModuleType

from jiig.constants import TOP_TASK_LABEL, SUB_TASK_LABEL, TOP_TASK_DEST_NAME
from jiig.driver import Driver, DriverOptions, CLIDriver
from jiig.util.class_resolver import ClassResolver


def load_driver(*,
                driver_spec: type | str | ModuleType | None,
                tool_name: str,
                global_option_names: list[str],
                description: str,
                ) -> Driver:
    """Create configured driver instance.

    Args:
        driver_spec: driver specification
        tool_name: tool name
        global_option_names: global option names
        description: tool description

    Returns:
        prepared driver
    """
    driver_options = DriverOptions(
        raise_exceptions=True,
        top_task_label=TOP_TASK_LABEL,
        sub_task_label=SUB_TASK_LABEL,
        top_task_dest_name=TOP_TASK_DEST_NAME,
        global_option_names=global_option_names,
    )
    if driver_spec is None:
        driver_spec = CLIDriver
    driver_resolver = ClassResolver(Driver, 'driver')
    driver_registration = driver_resolver.resolve_class(driver_spec)
    driver = driver_registration.subclass(tool_name,
                                          description,
                                          options=driver_options)
    return driver
