# Copyright (C) 2021-2022, Steven Cooper
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
from typing import Self


@dataclass
class RuntimeArguments:
    """Runtime arguments for driver and CLI."""
    cli: list[str]
    runner: list[str]
    driver: list[str]

    @classmethod
    def prepare(cls,
                runner_args: list[str] | None,
                cli_args: list[str] | None,
                ) -> Self:
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
        return cls(cli_args, runner_args, driver_args)
