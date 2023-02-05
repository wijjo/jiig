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
"""

import sys
from pathlib import Path

from .constants import JIIG_CONFIGURATION_NAME
from .util.log import abort
from .util.options import OPTIONS


def main(tool_root: Path | str,
         runner_args: list[str] = None,
         cli_args: list[str] = None,
         ):
    """
    Main function called from jiig script to drive tool and task initialization.

    Hides internal dependencies from external imports of this module by
    importing internal modules locally.

    :param tool_root: tool root folder
    :param runner_args: optional Jiig runner preamble, e.g. for jiig shebang usage
    :param cli_args: command line arguments to override the default, sys.argv[1:]
    """
    from .constants import CORE_PIP_PACKAGES
    from .util.log import set_log_writer
    from .util.python import install_missing_pip_packages
    from . import init

    if not isinstance(tool_root, Path):
        tool_root = Path(tool_root)
    jiig_root = Path(__file__).resolve().parent.parent

    # Prepare runtime arguments.
    runtime_args = init.prepare_runtime_arguments(runner_args, cli_args)

    # Prepare virtual environment, with possible restart (may not return!).
    venv_root = init.check_virtual_environment(
        tool_root=tool_root,
        arguments=runtime_args,
    )

    # Install any missing core Pip packages that are required for startup.
    install_missing_pip_packages(
        packages=CORE_PIP_PACKAGES,
        venv_folder=venv_root,
        quiet=True,
    )

    # Load tool and provide defaults for missing tool data.
    tool = init.load_tool(
        tool_root=tool_root,
        jiig_root=jiig_root,
    )

    # Add Jiig and tool library folders to Python library load path.
    for library_folder in tool.library_folders:
        if library_folder not in sys.path:
            sys.path.insert(0, library_folder)

    # If Jiig is not the tool, load the jiig tool for access to shared data.
    pip_packages = tool.meta.pip_packages
    if tool.paths.tool_root == tool.paths.jiig_root:
        jiig_tool = tool
    else:
        jiig_tool = init.load_tool(
            tool_root=jiig_root,
            jiig_root=jiig_root,
        )
        pip_packages.extend(jiig_tool.meta.pip_packages)

    # Install any other missing Pip packages that are needed by the tool.
    install_missing_pip_packages(
        packages=pip_packages,
        venv_folder=venv_root,
        quiet=True,
    )

    # Load driver.
    driver = init.load_driver(
        driver_spec=tool.custom.driver,
        tool_name=tool.meta.tool_name,
        global_option_names=tool.global_option_names,
        description=tool.meta.description,
    )

    # Use driver-provided log writer.
    set_log_writer(driver.get_log_writer())

    # Initialize driver and receive preliminary driver data.
    driver_prelim_data = driver.initialize_driver(
        command_line_arguments=runtime_args.driver,
    )

    # Apply options globally so that debug, etc. can be in effect below.
    tool.apply_options(driver_prelim_data.data)

    # Expand alias as needed and provide 'help' as default command.
    expanded_arguments = init.expand_arguments(
        arguments=driver_prelim_data.additional_arguments,
        tool_name=tool.meta.tool_name,
        paths=tool.paths,
        default_command='help',
    )

    if tool.paths.tool_root != tool.paths.jiig_root:
        # Inject built-in tasks into a tool other than Jiig.
        task_tree = init.inject_builtin_tasks(
            tool_task_tree=tool.task_tree,
            jiig_task_tree=jiig_tool.task_tree,
            tool_options=tool.options,
            paths=tool.paths,
        )
    else:
        # Jiig itself doesn't need built-in tasks injected.
        task_tree = tool.task_tree

    if OPTIONS.debug:
        task_tree.log_dump_all()

    # Prepare application runtime task tree.
    runtime_root_task = init.prepare_runtime_tasks(
        task_tree=task_tree,
    )

    # Get arguments data object from driver.
    driver_data = driver.initialize_application(
        arguments=expanded_arguments,
        root_task=runtime_root_task,
    )

    # Prepare help generator.
    help_generator = init.prepare_help_generator(
        driver=driver,
        root_task=runtime_root_task,
    )

    # Create standard or custom Runtime object to pass to task functions.
    runtime = init.prepare_runtime_object(
        runtime_spec=tool.custom.runtime,
        metadata=tool.meta,
        argument_data=driver_data.data,
        paths=tool.paths,
        help_generator=help_generator,
        extra_symbols=tool.extra_symbols,
    )

    # Execute application.
    init.execute_application(
        task_stack=driver_data.task_stack,
        argument_data=driver_data.data,
        runtime=runtime,
    )


def jiig_main(jiig_root: str | Path,
              runner_args: list[str],
              cli_args: list[str],
              ):
    """
    Main function for Jiig itself.

    :param jiig_root: Jiig root folder
    :param runner_args: runner arguments
    :param cli_args: command line arguments
    """
    main(
        jiig_root,
        runner_args=runner_args,
        cli_args=cli_args,
    )


def tool_main(runner_args: list[str],
              cli_args: list[str],
              ):
    """
    Main function for Jiig-based tools.

    :param runner_args: runner arguments
    :param cli_args: command line arguments
    """
    script_path = Path(runner_args[1]).resolve()
    tool_root = script_path.parent
    while not (tool_root / JIIG_CONFIGURATION_NAME).is_file():
        parent_folder = tool_root.parent
        if parent_folder == tool_root:
            abort(f'Jiig configuration not found: {JIIG_CONFIGURATION_NAME}')
        tool_root = parent_folder
    main(
        tool_root,
        runner_args=runner_args,
        cli_args=cli_args,
    )
