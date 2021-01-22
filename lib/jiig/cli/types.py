"""
Classes used for parsing the command line.
"""

from dataclasses import dataclass
from typing import Text, Union, Any, Sequence, List, Optional


class ArgumentParserError(Exception):
    pass


@dataclass
class ParserPositionalArgument:
    """
    Data for a parser positional argument.
    """
    name: Text
    description: Text
    cardinality: Union[int, Text] = None
    default_value: Any = None
    choices: Sequence = None


@dataclass
class ParserOption:
    """
    Data for a parser command option.
    """
    name: Text
    description: Text
    flags: Sequence[Text]
    is_boolean: bool = False
    cardinality: Union[int, Text] = None
    default_value: Any = None
    choices: Sequence = None


class ParserCommand:
    """
    Object/API for building a parser command.
    """

    def __init__(self,
                 name: Text,
                 description: Text,
                 ):
        """
        Command constructor.

        :param name: command name
        :param description: command description
        """
        self.name = name
        self.description = description
        self.positional_arguments: List[ParserPositionalArgument] = []
        self.options: List[ParserOption] = []
        self.sub_commands: List[ParserCommand] = []

    def add_sub_command(self,
                        name: Text,
                        description: Text,
                        ) -> 'ParserCommand':
        """
        Add a sub-command.

        :param name: command name
        :param description: command description
        :return: command object
        """
        sub_command = ParserCommand(name, description)
        self.sub_commands.append(sub_command)
        return sub_command

    def add_positional_argument(self,
                                name: Text,
                                description: Text,
                                cardinality: Union[int, Text] = None,
                                default_value: Any = None,
                                choices: Sequence = None,
                                ) -> ParserPositionalArgument:
        """
        Add a positional argument to current command/sub-command.

        :param name: argument name
        :param description: argument description
        :param cardinality: optional cardinality as count, '*', '+', or '?'
        :param default_value: optional default value
        :param choices: optional restricted value set as sequence
        :return: positional argument data object
        """
        positional_argument = ParserPositionalArgument(name,
                                                       description,
                                                       cardinality=cardinality,
                                                       default_value=default_value,
                                                       choices=choices)
        self.positional_arguments.append(positional_argument)
        return positional_argument

    def add_option(self,
                   name: Text,
                   description: Text,
                   flags: Sequence[Text],
                   is_boolean: bool = False,
                   cardinality: Union[int, Text] = None,
                   default_value: Any = None,
                   choices: Sequence = None,
                   ) -> ParserOption:
        """
        Add a positional argument to current command/sub-command.

        :param name: argument name
        :param description: argument description
        :param is_boolean: True for a boolean option flag,
                           where the value is True if the flag is present
        :param flags: option flags
        :param cardinality: optional cardinality as count, '*', '+', or '?'
        :param default_value: optional default value
        :param choices: optional restricted value set as sequence
        :return: option data object
        """
        option = ParserOption(name,
                              description,
                              flags,
                              is_boolean=is_boolean,
                              cardinality=cardinality,
                              default_value=default_value,
                              choices=choices)
        self.options.append(option)
        return option


class ParserRoot:
    def __init__(self):
        self.commands: List[ParserCommand] = []

    def add_command(self,
                    name: Text,
                    description: Text,
                    ) -> ParserCommand:
        """
        Add a top level command.

        :param name: command name
        :param description: command description
        :return: command object
        """
        command = ParserCommand(name, description)
        self.commands.append(command)
        return command


@dataclass
class PreParseResults:
    # Attributes received from options.
    data: object
    # Trailing arguments, following any options.
    trailing_arguments: List[Text]


@dataclass
class ParseResults:
    # Attributes received from options and arguments.
    data: object
    # Command names.
    names: List[Text]
    # Trailing arguments, if requested, following any options.
    trailing_arguments: Optional[List[Text]]


@dataclass
class CommandLineParseOptions:
    capture_trailing: bool = False
    raise_exceptions: bool = False
    disable_debug: bool = False
    disable_dry_run: bool = False
    disable_verbose: bool = False


class CommandLineParserImplementation:
    """
    Parser implementation interface.

    Methods below are mandatory overrides.
    """

    def on_pre_parse(self,
                     command_line_arguments: Sequence[Text],
                     options: CommandLineParseOptions,
                     ) -> PreParseResults:
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
                 root: ParserRoot,
                 options: CommandLineParseOptions,
                 ) -> ParseResults:
        """
        Mandatory override to parse the command line.

        :param command_line_arguments: command line argument list
        :param name: program name
        :param description: program description
        :param root: parser root object
        :param options: options governing parser building and execution
        :return: object with argument data attributes
        """
        raise NotImplementedError
