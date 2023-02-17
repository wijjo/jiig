#!/usr/bin/env python3
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
Jiig tool script runner.

Invoked by tool scripts where this is used as the shebang line interpreter.

The tool script generally has TOML tool configuration data.
"""

import os
import sys
from pathlib import Path

COMMAND_NAME = Path(__file__).stem


def _fatal(*messages: str):
    for message in messages:
        sys.stderr.write(f'FATAL: {message}{os.linesep}')
    sys.stderr.write(os.linesep)
    sys.exit(1)


def jiigrun_main(jiig_source_root: Path = None, check_venv: bool = False):
    """
    jiigrun script main.

    Checking for a virtual environment is optional, because when Jiig is
    installed it shouldn't require it, and a virtual environment may be provided
    by the user.

    :param jiig_source_root: optional source root provided by source tree bin/jiigrun
    :param check_venv: make sure to run in a Jiig virtual environment if True
    """
    runner_args = sys.argv[:2]
    cli_args = sys.argv[2:]
    if len(runner_args) < 2 or not os.path.isfile(runner_args[1]):
        _fatal('Expect the first command line argument to be a script file.',
               f'This will happen when "{COMMAND_NAME}" is used as a tool'
               ' script "shebang" line interpreter.')
    script_path = Path(runner_args[1]).resolve()
    from jiig.init.arguments import prepare_runtime_arguments
    runtime_args = prepare_runtime_arguments(runner_args, cli_args)
    from jiig.init.tool import load_tool_configuration
    tool = load_tool_configuration(script_path, False, jiig_source_root)
    from jiig.init.venv import check_virtual_environment
    if check_venv:
        check_virtual_environment(
            tool_name=tool.meta.tool_name,
            runner_args=runtime_args.runner,
            cli_args=runtime_args.cli,
        )
    from jiig.init.startup_main import startup_main
    startup_main(
        tool=tool,
        driver_args=runtime_args.driver,
        is_jiig=False,
    )


if __name__ == '__main__':
    jiigrun_main()
