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

"""
Jiig main function to boot the tool.

Consists of a series of function calls into the initialization package.

The `initializers` package modules each provide an `initialize()` function. The
`initialize()` function receives previously-loaded data, which it massages, as
needed, and applies to tool state, as appropriate.

Note that by convention `initializers` modules are either read-only or
write-only. Read-only modules are kept side-effect-free and return loaded data.
Write-only modules return no data.

Jiig module dependencies are imported locally (inside functions) to make this
module easy to import before library paths are configured.
"""

from jiig.tool import Tool
from jiig.util.log import set_log_writer
from jiig.util.options import OPTIONS
from jiig.util.python import install_missing_pip_packages

from .arguments import expand_arguments
from .builtin_tasks import inject_builtin_tasks
from .driver import load_driver
from .execution import execute_application
from .help import prepare_help_generator
from jiig.jiigadmin import (
    JIIGADMIN_META,
    JIIGADMIN_TASK_TREE,
)
from .library_path import prepare_library_path
from .runtime import prepare_runtime_object
from .runtime_tasks import prepare_runtime_tasks


def startup_main(tool: Tool,
                 driver_args: list[str],
                 is_jiig: bool,
                 ):
    """
    Common startup code to drive most of the initialization.

    tool is None if running Jiig directly.

    :param tool: tool runtime data, e.g. loaded from configuration
    :param driver_args: command line arguments prepared for driver
    :param is_jiig: True when running jiigadmin
    """
    # Need access to Jiig configuration for built-in tasks and library paths.
    if is_jiig:
        jiig_tool = tool
    else:
        jiig_tool = Tool(meta=JIIGADMIN_META, task_tree=JIIGADMIN_TASK_TREE)

    # Add (missing) Jiig and tool library folders to Python library load path.
    prepare_library_path(
        tool_source_root=tool.paths.tool_source_root,
        jiig_library_paths=jiig_tool.paths.libraries,
        additional_library_paths=tool.paths.libraries,
    )

    # Install any other missing Pip packages that are needed by the tool.
    install_missing_pip_packages(
        packages=tool.meta.pip_packages,
        venv_folder=tool.paths.venv,
        quiet=True,
    )

    # Load driver.
    driver = load_driver(
        driver_spec=tool.custom.driver,
        tool_name=tool.meta.tool_name,
        global_option_names=tool.global_option_names,
        description=tool.meta.description,
    )

    # Use driver-provided log writer.
    set_log_writer(driver.get_log_writer())

    # Initialize driver and receive preliminary driver data.
    driver_prelim_data = driver.initialize_driver(
        command_line_arguments=driver_args,
    )

    # Apply options globally so that debug, etc. can be in effect below.
    tool.apply_options(driver_prelim_data.data)

    # Expand alias as needed and provide 'help' as default command.
    expanded_arguments = expand_arguments(
        arguments=driver_prelim_data.additional_arguments,
        tool_name=tool.meta.tool_name,
        paths=tool.paths,
        default_command='help',
    )

    # Need access to Jiig configuration for built-in tasks and library paths.
    if not is_jiig:
        # Inject built-in tasks as needed.
        task_tree = inject_builtin_tasks(
            task_tree=tool.task_tree,
            jiig_task_tree=jiig_tool.task_tree,
            tool_options=tool.options,
        )
    else:
        task_tree = tool.task_tree

    if OPTIONS.debug:
        task_tree.log_dump_all()

    # Prepare application runtime task tree.
    runtime_root_task = prepare_runtime_tasks(
        task_tree=task_tree,
    )

    # Get arguments data object from driver.
    driver_data = driver.initialize_application(
        arguments=expanded_arguments,
        root_task=runtime_root_task,
    )

    # Prepare help generator.
    help_generator = prepare_help_generator(
        driver=driver,
        root_task=runtime_root_task,
    )

    # Create standard or custom Runtime object to pass to task functions.
    runtime = prepare_runtime_object(
        runtime_spec=tool.custom.runtime,
        metadata=tool.meta,
        argument_data=driver_data.data,
        paths=tool.paths,
        help_generator=help_generator,
        extra_symbols=tool.extra_symbols,
    )

    # Execute application.
    execute_application(
        task_stack=driver_data.task_stack,
        argument_data=driver_data.data,
        runtime=runtime,
    )
