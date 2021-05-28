"""CLI Base implementation class."""

from typing import Sequence, Text

from .cli_command import CLICommand
from .cli_types import CLIOptions, CLIPreliminaryResults, CLIResults


class CLIImplementation:
    """
    Parser implementation interface.

    Methods below are mandatory overrides.
    """

    def __init__(self):
        # These are set from the outside a little later.
        self.debug = False
        self.dry_run = False
        self.pause = False
        self.verbose = False
        self.top_task_dest_name = 'command'

    def on_pre_parse(self,
                     command_line_arguments: Sequence[Text],
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
                 command_line_arguments: Sequence[Text],
                 name: Text,
                 description: Text,
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
