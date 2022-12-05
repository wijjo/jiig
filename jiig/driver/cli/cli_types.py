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

"""Simple CLI types."""

from dataclasses import dataclass, field
from typing import Sequence

from ...util.general import DefaultValue
from ...util.repetition import Repetition


class CLIError(Exception):
    pass


@dataclass
class CLIOption:
    """Data for CLI command option."""
    name: str
    description: str
    flags: Sequence[str]
    is_boolean: bool = False
    repeat: Repetition = None
    default: DefaultValue = None
    choices: Sequence = None


@dataclass
class CLIOptions:
    """CLI processing options."""
    capture_trailing: bool = False
    raise_exceptions: bool = False
    global_options: list[CLIOption] = field(default_factory=list)


@dataclass
class CLIPositional:
    """Data for CLI positional argument."""
    name: str
    description: str
    repeat: Repetition = None
    default: DefaultValue = None
    choices: Sequence = None


@dataclass
class CLIPreliminaryResults:
    """Results from preliminary CLI argument parsing."""
    # Attributes received from options.
    data: object
    # Trailing arguments, following any options.
    trailing_arguments: list[str]


@dataclass
class CLIResults:
    """Results from full CLI argument parsing."""
    # Attributes received from options and arguments.
    data: object
    # Command names.
    names: list[str]
    # Trailing arguments, if requested, following any options.
    trailing_arguments: list[str] | None
