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

import sys
from types import ModuleType

from jiig.constants import TOP_TASK_LABEL, SUB_TASK_LABEL, TOP_TASK_DEST_NAME
from jiig.driver import Driver, DriverOptions, CLIDriver
from jiig.types import ToolOptions
from jiig.util.class_resolver import ClassResolver
from jiig.util.log import set_log_writer
from jiig.util.options import OPTIONS


def prepare_driver(*,
                   driver_spec: type | str | ModuleType | None,
                   args: list[str] | None,
                   tool_name: str,
                   options: ToolOptions,
                   description: str,
                   ) -> Driver:
    """Create configured driver instance.

    Args:
        driver_spec: driver specification
        args: command line arguments
        tool_name: tool name
        options: tool options
        description: tool description

    Returns:
        prepared driver
    """
    global_option_names: list[str] = []
    if not options.disable_debug:
        global_option_names.append('debug')
    if not options.disable_dry_run:
        global_option_names.append('dry_run')
    if not options.disable_verbose:
        global_option_names.append('verbose')
    if options.enable_pause:
        global_option_names.append('pause')
    if options.enable_keep_files:
        global_option_names.append('keep_files')

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

    # Use driver-provided log writer.
    set_log_writer(driver.get_log_writer())

    # Initialize driver and receive preliminary driver data.
    # Filter out leading '--' used when restarting in virtual environment.
    if args is None:
        args = sys.argv[1:]
    if args and args[0] == '--':
        args = args[1:]
    driver.initialize_driver(args)

    # Update global util options so that they are in effect upon returning.
    if not options.disable_debug and getattr(driver.preliminary_app_data.data, 'DEBUG'):
        OPTIONS.set_debug(True)
    if not options.disable_dry_run and getattr(driver.preliminary_app_data.data, 'DRY_RUN'):
        OPTIONS.set_dry_run(True)
    if not options.disable_verbose and getattr(driver.preliminary_app_data.data, 'VERBOSE'):
        OPTIONS.set_verbose(True)
    if options.enable_pause and getattr(driver.preliminary_app_data.data, 'PAUSE'):
        OPTIONS.set_pause(True)
    if options.enable_keep_files and getattr(driver.preliminary_app_data.data, 'KEEP_FILES'):
        OPTIONS.set_keep_files(True)

    return driver
