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

"""CLI Base implementation class."""

from typing import Sequence

from .cli_command import CLICommand
from .cli_types import CLIOptions, CLIPreliminaryResults, CLIResults


class CLIImplementation:
    """
    Parser implementation interface.

    Methods below are mandatory overrides.
    """

    def __init__(self):
        # Set from outside after construction.
        self.top_task_dest_name = 'command'

    def on_pre_parse(self,
                     command_line_arguments: Sequence[str],
                     options: CLIOptions,
                     ) -> CLIPreliminaryResults:
        """
        Mandatory override to pre-parse the command line.

        :param command_line_arguments: command line argument list
        :param options: options governing parser building and execution
        :return: (object with argument data attributes, trailing argument list) tuple
        """
        raise NotImplementedError

    def on_parse(self,
                 command_line_arguments: Sequence[str],
                 name: str,
                 description: str,
                 root_command: CLICommand,
                 options: CLIOptions,
                 ) -> CLIResults:
        """
        Mandatory override to parse the command line.

        :param command_line_arguments: command line argument list
        :param name: program name
        :param description: program description
        :param root_command: root command
        :param options: options governing parser building and execution
        :return: object with argument data attributes
        """
        raise NotImplementedError
