"""
Base command line parser.
"""

from typing import Text, Optional, Sequence

from .options import ParserImplementations
from .types import ParserRoot, CommandLineParseOptions, CommandLineParserImplementation, \
    PreParseResults, ParseResults


def _get_implementation(implementation: Text) -> CommandLineParserImplementation:
    if implementation is None:
        from .implementations import argparse
        parser_module = argparse
    else:
        if not hasattr(ParserImplementations, implementation):
            raise ValueError(f'Unsupported CLI parser implementation "{implementation}".')
        from jiig.cli_parsing.implementations import argparse
        parser_module = argparse
    return parser_module.get_implementation()


class CommandLineParserDriver:

    def __init__(self,
                 name: Text,
                 description: Text,
                 implementation: CommandLineParserImplementation,
                 disable_debug: bool = False,
                 disable_dry_run: bool = False,
                 disable_verbose: bool = False,
                 ):
        """
        Command line parser manager constructor.

        :param name: tool name
        :param description: tool description
        :param implementation: parser implementation
        :param disable_debug: disable the debug option if True
        :param disable_dry_run: disable the dry run option if True
        :param disable_verbose: disable the verbose option if True
        """
        self.name = name
        self.description = description
        self.implementation = implementation
        self.disable_debug = disable_debug
        self.disable_dry_run = disable_dry_run
        self.disable_verbose = disable_verbose
        self.root: Optional[ParserRoot] = None

    def pre_parse(self,
                  command_line_arguments: Sequence[Text],
                  raise_exceptions: bool = False,
                  ) -> PreParseResults:
        """
        Pre-parse the command line.

        :param command_line_arguments: command line argument list
        :param raise_exceptions: raise exceptions if True
        :return: data updated by parser implementation
        """
        options = CommandLineParseOptions(raise_exceptions=raise_exceptions,
                                          disable_debug=self.disable_debug,
                                          disable_dry_run=self.disable_dry_run,
                                          disable_verbose=self.disable_verbose)
        return self.implementation.on_pre_parse(command_line_arguments, options)

    def initialize_parser(self) -> ParserRoot:
        """
        Start building the parser.

        :return: parser root interface
        """
        self.root = ParserRoot()
        return self.root

    def parse(self,
              command_line_arguments: Sequence[Text],
              capture_trailing: bool = False,
              raise_exceptions: bool = False,
              ) -> ParseResults:
        """
        Parse the command line.

        :param command_line_arguments: command line argument list
        :param capture_trailing: allow and capture trailing arguments if True
        :param raise_exceptions: raise exceptions if True
        :return: data updated by parser implementation
        """
        if self.root is None:
            raise RuntimeError('Called CommandLineParser.parser() was called without'
                               ' initialize_parser() ever having been called.')
        options = CommandLineParseOptions(capture_trailing=capture_trailing,
                                          raise_exceptions=raise_exceptions,
                                          disable_debug=self.disable_debug,
                                          disable_dry_run=self.disable_dry_run,
                                          disable_verbose=self.disable_verbose)
        return self.implementation.on_parse(command_line_arguments,
                                            self.name,
                                            self.description,
                                            self.root,
                                            options)


def get_parser_driver(name: Text,
                      description: Text,
                      implementation: Text = None,
                      disable_debug: bool = False,
                      disable_dry_run: bool = False,
                      disable_verbose: bool = False,
                      ) -> CommandLineParserDriver:
    """
    Command line parser manager constructor.

    :param name: tool name
    :param description: tool description
    :param implementation: implementation name (ParserImplementations has valid values)
    :param disable_debug: disable debug option
    :param disable_dry_run: disable dry run option
    :param disable_verbose: disable verbose option
    """
    implementation = _get_implementation(implementation)
    parser = CommandLineParserDriver(name,
                                     description,
                                     implementation,
                                     disable_debug=disable_debug,
                                     disable_dry_run=disable_dry_run,
                                     disable_verbose=disable_verbose)
    return parser
