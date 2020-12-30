"""
CLI parser based on argparse standard library module.
"""

import argparse
import os
from contextlib import contextmanager
from typing import List, Text, Sequence, Tuple, Union, Any, Dict

from jiig.utility.console import abort, log_message
from jiig.utility.general import make_list
from jiig.utility.python import format_call_string

from .. import options
from ..types import ArgumentParserError, ParserRoot, CommandLineParseOptions, \
    CommandLineParserImplementation, PreParseResults, ParseResults, ParserCommand

DEST_NAME_SEPARATOR = '.'


class _ArgumentParser(argparse.ArgumentParser):
    """Wrap the argparse class to add debugging and some default values."""

    raise_exceptions = False

    def __init__(self,
                 prog: Text = None,
                 description: Text = None,
                 add_help: bool = False,
                 ):
        try:
            super().__init__(prog=prog, description=description, add_help=add_help)
            self._dump('ArgumentParser', prog=prog, description=description)
        except Exception as exc:
            self._abort('ArgumentParser', exc)

    def add_subparsers(self, *args, **kwargs):
        """
        Overridden for logging and exception handling.

        :param args: argparse.ArgumentParser.add_subparsers() positional arguments
        :param kwargs: argparse.ArgumentParser.add_subparsers() keyword arguments
        """
        self._dump('add_subparsers', *args, **kwargs)
        try:
            _parser = self
            _group = super().add_subparsers(*args, **kwargs)

            class _GroupWrapper:

                @staticmethod
                def add_parser(*group_args, **group_kwargs):
                    sub_parser = _group.add_parser(*group_args, **group_kwargs)
                    if options.DEBUG:
                        _parser._dump('add_parser', *args, **kwargs,
                                      returned=f'ArgumentParser({id(sub_parser)})')
                    return sub_parser

                def __getattr__(self, name):
                    return getattr(_group, name)

                def __setattr__(self, name, value):
                    setattr(_group, name, value)

            return _GroupWrapper()
        except Exception as exc:
            self._abort('add_subparsers', exc, *args, **kwargs)

    def add_argument(self, *args, **kwargs):
        """
        Overridden for logging and exception handling.

        :param args: argparse.ArgumentParser.add_argument() positional arguments
        :param kwargs: argparse.ArgumentParser.add_argument() keyword arguments
        """
        # Remove any keywords that argparse does not handle.
        if 'common_footnotes' in kwargs:
            del kwargs['common_footnotes']
        if options.DEBUG:
            self._dump('add_argument', *args, **kwargs)
        try:
            return super().add_argument(*args, **kwargs)
        except Exception as exc:
            self._abort('add_argument', exc, *args, **kwargs)

    def parse_args(self,
                   args: Sequence = None,
                   namespace: argparse.Namespace = None,
                   raise_exceptions: bool = False
                   ) -> argparse.Namespace:
        """
        Overridden for logging and exception handling.

        :param args: command line arguments
        :param namespace: incoming namespace
        :param raise_exceptions: raise exceptions if True
        """
        if options.DEBUG:
            self._dump('parse_args',
                       args=args,
                       namespace=namespace,
                       raise_exceptions=raise_exceptions)
        if raise_exceptions:
            with self._exceptions():
                return super().parse_args(args=args, namespace=namespace)
        else:
            return super().parse_args(args=args, namespace=namespace)

    def parse_known_args(self,
                         args: Sequence = None,
                         namespace: argparse.Namespace = None,
                         raise_exceptions: bool = False
                         ) -> Tuple[argparse.Namespace, List[Text]]:
        """
        Overridden for logging and exception handling.

        :param args: command line arguments
        :param namespace: incoming namespace
        :param raise_exceptions: raise exceptions if True
        """
        if options.DEBUG:
            self._dump('parse_known_args',
                       args=args,
                       namespace=namespace,
                       raise_exceptions=raise_exceptions)
        if raise_exceptions:
            with self._exceptions():
                return super().parse_known_args(args=args, namespace=namespace)
        else:
            return super().parse_known_args(args=args, namespace=namespace)

    def error(self, message: Text):
        """
        Error handling.

        :param message: error message
        """
        if self.raise_exceptions:
            raise ArgumentParserError(message)
        # if REQUIRED_SUB_COMMAND_RE.match(message):
        #     words = self.prog.split()
        #     if len(words) == 1:
        #         lines = [f'The "{words[0]}" program requires a command.',
        #                  f'See "{words[0]} help" for more information.', ]
        #     else:
        #         lines = [f'The "{self.prog}" command requires a sub-command.',
        #                  f'See "{" ".join(words[:-1])} help {words[-1]}" for more information.']
        #     for line in lines:
        #         sys.stderr.write(line)
        #         sys.stderr.write(os.linesep)
        #     sys.exit(0)
        super().error(message)

    def format_usage(self):
        return f'(see tool help for more information){os.linesep}'

    def format_help(self):
        return super().format_help()

    def _dump(self, method_name, *args, **kwargs):
        if options.DEBUG:
            log_message(f'ArgumentParser[{id(self)}]: {format_call_string(method_name, *args, **kwargs)}')

    @staticmethod
    def _abort(method_name, exc, *args, **kwargs):
        abort(f'argparse: {format_call_string(method_name, *args, **kwargs)})',
              exception=exc)

    @classmethod
    @contextmanager
    def _exceptions(cls):
        cls.raise_exceptions = True
        try:
            yield
        finally:
            cls.raise_exceptions = False


class ArgparseImplementation(CommandLineParserImplementation):

    def __init__(self):
        super().__init__()
        self.parsers: Dict[Text, argparse.ArgumentParser] = {}

    def on_pre_parse(self,
                     command_line_arguments: Sequence[Text],
                     parse_options: CommandLineParseOptions,
                     ) -> PreParseResults:
        """
        Mandatory override to pre-parse the command line.

        :param command_line_arguments: command line argument list
        :param parse_options: options governing parser building and execution
        :return: (object with argument data attributes, trailing argument list) tuple
        """
        # Don't use the primary argparse parser, since it may be initialized later.
        pre_parser = _ArgumentParser()
        self._add_top_level_options(pre_parser, parse_options)
        data, trailing_arguments = pre_parser.parse_known_args(
            command_line_arguments, raise_exceptions=parse_options.raise_exceptions)
        return PreParseResults(data, trailing_arguments)

    def on_parse(self,
                 command_line_arguments: Sequence[Text],
                 name: Text,
                 description: Text,
                 root: ParserRoot,
                 parse_options: CommandLineParseOptions,
                 ) -> ParseResults:
        """
        Mandatory override to parse the command line.

        :param command_line_arguments: command line argument list
        :param name: program name
        :param description: program description
        :param root: parser root object
        :param parse_options: options governing parser building and execution
        :return: object with argument data attributes
        """
        parser = _ArgumentParser(name, description)
        self._add_top_level_options(parser, parse_options)
        self.parsers[options.TOP_COMMAND_LABEL] = parser

        top_group = parser.add_subparsers(dest=options.TOP_COMMAND_LABEL,
                                          metavar=options.TOP_COMMAND_LABEL,
                                          required=True)
        for command in root.commands:
            sub_parser = top_group.add_parser(command.name,
                                              help=command.description,
                                              add_help=False)
            self._prepare_recursive(command, sub_parser, options.TOP_COMMAND_LABEL)

        # Parse the command line arguments.
        if parse_options.capture_trailing:
            args, trailing_args = parser.parse_known_args(command_line_arguments)
        else:
            args = parser.parse_args(command_line_arguments)
            trailing_args: List[Text] = []

        # Determine the active command names.
        command_dest_preamble = options.TOP_COMMAND_LABEL + DEST_NAME_SEPARATOR
        command_dest = ''
        for dest in dir(args):
            if ((dest == options.TOP_COMMAND_LABEL or
                 dest.startswith(command_dest_preamble)) and len(dest) > len(command_dest)):
                command_dest = dest
        if not command_dest:
            raise RuntimeError(f'Missing {options.TOP_COMMAND_LABEL}* member'
                               f' in argparse namespace: {args}')
        names = [name.lower() for name in command_dest.split(DEST_NAME_SEPARATOR)[1:]]
        names.append(getattr(args, command_dest))
        return ParseResults(args, names, trailing_args)

    @staticmethod
    def _add_top_level_options(parser: argparse.ArgumentParser,
                               parse_options: CommandLineParseOptions,
                               ):
        if not parse_options.disable_debug:
            parser.add_argument('--debug', dest='DEBUG', action='store_true',
                                help='enable debug mode')
        if not parse_options.disable_dry_run:
            parser.add_argument('--dry-run', dest='DRY_RUN', action='store_true',
                                help='display actions without executing (dry run)')
        if not parse_options.disable_verbose:
            parser.add_argument('-v', dest='VERBOSE', action='store_true',
                                help='display additional (verbose) messages')

    @staticmethod
    def _add_option_or_argument(parser: argparse.ArgumentParser,
                                name: Text,
                                description: Text,
                                flags: Sequence[Text] = None,
                                is_boolean_option: bool = False,
                                cardinality: Union[int, Text] = None,
                                default_value: Any = None,
                                choices: Sequence = None,
                                ):
        kwargs = {'dest': name, 'help': description}
        if is_boolean_option:
            kwargs['action'] = 'store_true'
        if cardinality:
            kwargs['nargs'] = cardinality
        if default_value is not None:
            kwargs['default'] = default_value
        if choices:
            kwargs['choices'] = choices
        parser.add_argument(*make_list(flags), **kwargs)

    @classmethod
    def _prepare_recursive(cls,
                           command: ParserCommand,
                           parser: argparse.ArgumentParser,
                           parent_dest_name: Text,
                           ):
        for option in command.options:
            cls._add_option_or_argument(parser,
                                        option.name,
                                        option.description,
                                        flags=option.flags,
                                        is_boolean_option=option.is_boolean,
                                        cardinality=option.cardinality,
                                        default_value=option.default_value,
                                        choices=option.choices)
        for argument in command.positional_arguments:
            cls._add_option_or_argument(parser,
                                        argument.name,
                                        argument.description,
                                        cardinality=argument.cardinality,
                                        default_value=argument.default_value,
                                        choices=argument.choices)
        if command.sub_commands:
            dest_name = DEST_NAME_SEPARATOR.join([parent_dest_name, command.name.upper()])
            sub_group = parser.add_subparsers(dest=dest_name,
                                              metavar=options.SUB_COMMAND_LABEL,
                                              required=True)
            for sub_command in command.sub_commands:
                sub_parser = sub_group.add_parser(sub_command.name,
                                                  help=sub_command.description,
                                                  add_help=False)
                cls._prepare_recursive(sub_command, sub_parser, dest_name)


def get_implementation() -> CommandLineParserImplementation:
    """
    Required function to provide the implementation object.

    :return: implementation object
    """
    return ArgparseImplementation()
