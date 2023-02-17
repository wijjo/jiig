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
Startup main function for tools providing Tool data directly.
"""

import sys

from .task import TaskTree
from .tool import (
    Tool,
    ToolCustomizations,
    ToolMetadata,
    ToolOptions,
    ToolPaths,
)


def tool_main(meta: ToolMetadata,
              task_tree: TaskTree,
              options: ToolOptions = None,
              paths: ToolPaths = None,
              custom: ToolCustomizations = None,
              args: list = None,
              is_jiig: bool = False,
              ):
    """
    Start a Jiig tool application based on Python tool data.

    :param meta: tool metadata
    :param task_tree: task tree
    :param options: tool options
    :param paths: tool paths
    :param custom: optional tool customizations
    :param args: optional argument list (default: sys.argv[1:])
    :param is_jiig: True when running jiigadmin
    """
    if args is None:
        args = sys.argv[1:]
    from jiig.init.arguments import prepare_runtime_arguments
    runtime_args = prepare_runtime_arguments(args, args)
    tool = Tool(
        options=options or ToolOptions(),
        custom=custom or ToolCustomizations(None, None),
        meta=meta,
        paths=paths,
        task_tree=task_tree,
        extra_symbols={},
    )
    from jiig.init.startup_main import startup_main
    startup_main(
        tool=tool,
        driver_args=runtime_args.driver,
        is_jiig=is_jiig,
    )
