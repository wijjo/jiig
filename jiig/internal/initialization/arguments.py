# Copyright (C) 2023, Steven Cooper
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

"""Alias expansion."""

from jiig.task import RuntimeTask
from jiig.util.collections import make_list
from jiig.util.scoped_catalog import ScopedCatalog


def prepare_arguments(
    arguments: list[str],
    aliases_catalog: ScopedCatalog,
    runtime_root_task: RuntimeTask,
) -> list[str]:
    """Expand alias or provide default command, as needed.

    Args:
        arguments: input arguments to expand
        aliases_catalog: aliases catalog instance
        runtime_root_task: runtime root task (for finding aliases task group)

    Returns:
        expanded argument list
    """
    expanded_arguments: list[str] = []
    if arguments:
        if aliases_catalog.exists(arguments[0]):
            catalog_result = aliases_catalog.get(arguments[0])
            command_args: list[str] = [
                str(arg)
                for arg in make_list(catalog_result.found_payload)
            ]
            expanded_arguments = command_args + arguments[1:]
        else:
            expanded_arguments = arguments
    if not expanded_arguments:
        expanded_arguments = ['help']
    # Don't assume alias sub-command is present or that it's called 'alias'.
    alias_command_name: str | None = None
    for sub_task in runtime_root_task.sub_tasks:
        if (sub_task.task_function is not None
                and sub_task.task_function.__name__ == 'alias'):
            alias_command_name = sub_task.name
    # Special-purpose alias tweak to make sure aliased command arguments are
    # preceded by '--', as needed to avoid argument parsing errors due to
    # unknown command line options.
    if (alias_command_name is not None
            and len(expanded_arguments) > 3
            and expanded_arguments[0] == alias_command_name
            and not expanded_arguments[1].startswith('-')
            and not expanded_arguments[2].startswith('-')
            and '--' not in expanded_arguments[3:]):
        expanded_arguments = expanded_arguments[:3] + ['--'] + expanded_arguments[3:]
    return expanded_arguments
