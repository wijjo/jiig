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

"""Simple CLI types."""

from dataclasses import dataclass
from typing import Sequence

from jiig.util.default import DefaultValue
from jiig.util.repetition import Repetition


@dataclass
class CLIOptionArgument:
    """Data for CLI command option."""
    name: str
    description: str
    flags: Sequence[str]
    is_boolean: bool = False
    repeat: Repetition = None
    default: DefaultValue = None
    choices: Sequence = None


@dataclass
class CLIPositionalArgument:
    """Data for CLI positional argument."""
    name: str
    description: str
    repeat: Repetition = None
    default: DefaultValue = None
    choices: Sequence = None


class CLICommand:
    """CLI command."""
    def __init__(self,
                 name: str,
                 description: str,
                 visibility: int,
                 ):
        """
        Command constructor.

        :param name: command name
        :param description: command description
        :param visibility: 0=normal, 1=secondary, 2=hidden
        """
        self.name = name
        self.description = description
        self.visibility = visibility
        self.positionals: list[CLIPositionalArgument] = []
        self.options: list[CLIOptionArgument] = []
        self.sub_commands: list[CLICommand] = []
