"""CLI Parser command class."""

from typing import Text, List, Sequence

from jiig.util.general import DefaultValue
from jiig.util.repetition import Repetition

from .cli_types import CLIPositional, CLIOption


class CLICommand:
    """Object/API for building a parser command."""

    def __init__(self, name: Text, description: Text, visibility: int):
        """
        Command constructor.

        :param name: command name
        :param description: command description
        :param visibility: 0=normal, 1=secondary, 2=hidden
        """
        self.name = name
        self.description = description
        self.visibility = visibility
        self.positionals: List[CLIPositional] = []
        self.options: List[CLIOption] = []
        self.sub_commands: List[CLICommand] = []

    def add_sub_command(self, name: Text, description: Text, visibility: int) -> 'CLICommand':
        """
        Add a sub-command.

        :param name: command name
        :param description: command description
        :param visibility: 0=normal, 1=secondary, 2=hidden
        :return: command object
        """
        sub_command = CLICommand(name, description, visibility)
        self.sub_commands.append(sub_command)
        return sub_command

    def add_positional(self,
                       name: Text,
                       description: Text,
                       repeat: Repetition = None,
                       default: DefaultValue = None,
                       choices: Sequence = None,
                       ) -> CLIPositional:
        """
        Add a positional argument to current command/sub-command.

        :param name: argument name
        :param description: argument description
        :param repeat: optional repeat count or range (tuple pair)
        :param default: optional default value
        :param choices: optional restricted value set as sequence
        :return: positional argument data object
        """
        positional = CLIPositional(name,
                                   description,
                                   repeat=repeat,
                                   default=default,
                                   choices=choices)
        self.positionals.append(positional)
        return positional

    def add_option(self,
                   name: Text,
                   description: Text,
                   flags: Sequence[Text],
                   is_boolean: bool = False,
                   repeat: Repetition = None,
                   default: DefaultValue = None,
                   choices: Sequence = None,
                   ) -> CLIOption:
        """
        Add a positional argument to current command/sub-command.

        :param name: argument name
        :param description: argument description
        :param is_boolean: True for a boolean option flag,
                           where the value is True if the flag is present
        :param flags: option flags
        :param repeat: optional repeat count or range (tuple pair)
        :param default: optional default value
        :param choices: optional restricted value set as sequence
        :return: option data object
        """
        option = CLIOption(name,
                           description,
                           flags,
                           is_boolean=is_boolean,
                           repeat=repeat,
                           default=default,
                           choices=choices)
        self.options.append(option)
        return option
