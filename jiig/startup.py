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

"""Startup main functions.

tool_main(): Called by pure Python tools with pre-populated Tool data.

jiig_run(): Called by scripts using `jiig_run` as the "shebang" line
interpreter. Tool data is populated based on configuration information embedded
in the tool script.
"""

import os
import sys
from pathlib import Path

from .task import TaskTree
from .tool import (
    Tool,
    ToolCustomizations,
    ToolMetadata,
    ToolOptions,
    ToolPaths,
)


def _fatal(*messages: str):
    for message in messages:
        sys.stderr.write(f'FATAL: {message}{os.linesep}')
    sys.stderr.write(os.linesep)
    sys.exit(1)


def tool_main(meta: ToolMetadata,
              task_tree: TaskTree,
              options: ToolOptions = None,
              paths: ToolPaths = None,
              custom: ToolCustomizations = None,
              args: list = None,
              is_jiig: bool = False,
              skip_venv_check: bool = False,
              ):
    """Start a Jiig tool application based on Python tool data objects.

    This function is used by pure Python tools that can provide all the tool and
    task data.

    Args:
        meta: tool metadata
        task_tree: task tree
        options: tool options
        paths: tool paths
        custom: optional tool customizations
        args: optional argument list (default: sys.argv[1:])
        is_jiig: True when running jiigadmin
        skip_venv_check: skip check for running in a Jiig virtual environment if
            True
    """
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
        runner_args=sys.argv[:1],
        cli_args=args if args is not None else sys.argv[1:],
        is_jiigadmin=is_jiig,
        skip_venv_check=skip_venv_check,
    )


def jiigrun_main(jiig_source_root: Path = None,
                 skip_venv_check: bool = False,
                 ):
    """jiigrun script main.

    Called by tool scripts having "jiigrun" as the "shebang" line interpreter.
    The script's embedded configuration serves as the basis for generating tool
    runtime data.

    Checking for a virtual environment is optional, because when Jiig is
    installed it shouldn't require it, and a virtual environment may be provided
    by the user.

    Args:
        jiig_source_root: optional source root provided by source tree
            bin/jiigrun
        skip_venv_check: skip check for running in a Jiig virtual environment if
            True
    """
    runner_args = sys.argv[:2]
    cli_args = sys.argv[2:]
    if len(runner_args) < 2 or not os.path.isfile(runner_args[1]):
        _fatal('This program should only be used as a script "shebang" line interpreter.')
    script_path = Path(runner_args[1]).resolve()
    from jiig.init.tool import load_tool_configuration
    tool = load_tool_configuration(script_path, False, jiig_source_root)
    from jiig.init.startup_main import startup_main
    startup_main(
        tool=tool,
        runner_args=runner_args,
        cli_args=cli_args,
        is_jiigadmin=False,
        skip_venv_check=skip_venv_check,
    )
