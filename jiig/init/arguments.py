# Copyright (C) 2021-2023, Steven Cooper
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
Runtime arguments, e.g. for CLI.
"""

import sys
from dataclasses import dataclass

from jiig.tool import ToolPaths
from jiig.util.alias_catalog import is_alias_name, open_alias_catalog
from jiig.util.log import abort


@dataclass
class RuntimeArguments:
    """Runtime arguments for driver and CLI."""
    cli: list[str]
    runner: list[str]
    driver: list[str]


def prepare_runtime_arguments(runner_args: list[str] | None,
                              cli_args: list[str] | None,
                              ) -> RuntimeArguments:
    """
    Prepare runtime arguments.

    :param runner_args: runner arguments
    :param cli_args: CLI arguments
    :return: RuntimeArguments instance
    """
    # Filter out leading '--' used when restarting in virtual environment.
    if runner_args is None:
        runner_args = []
    if cli_args is None:
        cli_args = sys.argv[1:]
    if cli_args and cli_args[0] == '--':
        driver_args = cli_args[1:]
    else:
        driver_args = cli_args
    return RuntimeArguments(cli_args, runner_args, driver_args)


def expand_arguments(arguments: list[str],
                     tool_name: str,
                     paths: ToolPaths,
                     default_command: str,
                     ) -> list[str]:
    """
    Expand alias as needed to produce final argument list.

    :param arguments: argument list, possibly preceded by alias
    :param tool_name: tool name
    :param paths: runtime paths
    :param default_command: default command name used when no arguments are provided
    :return: expanded argument list
    """
    expanded_arguments: list[str] = []
    if arguments:
        if not is_alias_name(arguments[0]):
            expanded_arguments.extend(arguments)
        else:
            with open_alias_catalog(tool_name, paths.aliases) as alias_catalog:
                alias = alias_catalog.get_alias(arguments[0])
                if not alias:
                    abort(f'Alias "{arguments[0]}" not found.')
                expanded_arguments = alias.command + arguments[1:]
    if not expanded_arguments:
        expanded_arguments = [default_command]
    return expanded_arguments

