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

"""Task tree initialization."""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from jiig.constants import JIIG_TOOL_NAME
from jiig.util.log import abort
from jiig.util.python import (
    ModuleReferenceResolver,
    find_package_base_folder,
)


@dataclass
class ToolEnvironment:
    """Tool environment data collected from folders containing script."""
    #: Tool base folder.
    base_folder: Path
    #: Tool tasks package (module).
    tool_tasks_package: ModuleType
    #: Jiig tasks package (module or None if the tool is Jiig itself).
    jiig_tasks_package: ModuleType | None


def prepare_tool_environment(
    tool_name: str,
    script_path: Path,
) -> ToolEnvironment:
    """Prepare runtime task tree.

    Args:
        tool_name: tool name
        script_path: script path to help find tool package

    Returns:
        tool environment data
    """
    # First check if the task package can already be loaded.
    tasks_package_name = f'{tool_name}.tasks'
    module_resolver = ModuleReferenceResolver()
    resolved_tasks_package = module_resolver.resolve(tasks_package_name, optional=True)
    if resolved_tasks_package is None:
        # If it can't be loaded search up the folder hierarchy from the script
        # location to find the tasks package folder.
        tool_package_base_folder = find_package_base_folder(tasks_package_name,
                                                            script_path)
        if tool_package_base_folder is None:
            abort('Unable to locate tool package folder.')
        # Insert the tool package base folder into the Python load path and try
        # resolving the module again.
        sys.path.insert(0, str(tool_package_base_folder))
        resolved_tasks_package = module_resolver.resolve(tasks_package_name,
                                                         optional=True)
        if resolved_tasks_package is None:
            abort('Failed to load tasks package.', tasks_package_name)
    else:
        # If the tasks package is resolved, assume the base folder is the one
        # containing tasks parent package folder. Account for package.__file__
        # referencing the __init__.py file.
        package_path = Path(os.path.dirname(resolved_tasks_package.__file__)).resolve()
        tool_package_base_folder = package_path.parent.parent
    # If the tool isn't Jiig, need the Jiig package to resolve built-in tasks.
    if tool_name != JIIG_TOOL_NAME:
        resolved_jiig_tasks_package = module_resolver.resolve(f'{JIIG_TOOL_NAME}.tasks')
    else:
        resolved_jiig_tasks_package = None
    return ToolEnvironment(
        tool_package_base_folder,
        resolved_tasks_package,
        resolved_jiig_tasks_package,
    )
