"""
Argument parsing support.
"""

from __future__ import annotations
import argparse
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, List, Text, Dict, Sequence, Tuple

from jiig.internal import registry, global_data
from jiig.task_runner import HelpFormatter
from jiig.utility import append_dest_name, make_dest_name, log_message, abort, format_call_string,\
    metavar_to_dest_name

# Expose Namespace, since it's pretty generic, so that other modules don't need
# to know about argparse.
Namespace = argparse.Namespace

# Expression for making a friendlier error message for missing sub-task.
REQUIRED_SUB_TASK_RE = re.compile(fr'^(.* required: )' 
                                  fr'({global_data.CLI_DEST_NAME_PREFIX}'
                                  fr'|[A-Z_]+_{global_data.CLI_METAVAR_SUFFIX})$')


class ArgumentParserError(Exception):
    pass


class ArgumentParser(argparse.ArgumentParser):
    """Wrap a few functions for debug output."""

    raise_exceptions = False

    def __init__(self, *args, **kwargs):
        """
        Overridden for logging and exception handling.

        :param args: argparse.ArgumentParser() positional arguments
        :param kwargs: argparse.ArgumentParser() keyword arguments
        """
        self._dump('ArgumentParser', *args, **kwargs)
        try:
            super().__init__(*args, **kwargs)
        except Exception as exc:
            self._abort('ArgumentParser', exc, *args, **kwargs)

    def add_subparsers(self, *args, **kwargs):
        """
        Overridden for logging and exception handling.

        :param args: argparse.ArgumentParser.add_subparsers() positional arguments
        :param kwargs: argparse.ArgumentParser.add_subparsers() keyword arguments
        """
        self._dump('add_subparsers', *args, **kwargs)
        try:
            return super().add_subparsers(*args, **kwargs)
        except Exception as exc:
            self._abort('add_subparsers', exc, *args, **kwargs)

    def add_argument(self, *args, **kwargs):
        """
        Overridden for logging and exception handling.

        :param args: argparse.ArgumentParser.add_argument() positional arguments
        :param kwargs: argparse.ArgumentParser.add_argument() keyword arguments
        """
        if global_data.DEBUG:
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
        if global_data.DEBUG:
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
        if global_data.DEBUG:
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
        super().error(self._customize_error_message(message))

    @staticmethod
    def _customize_error_message(message: Text) -> Text:
        # Make other appropriate _error messages include the valid sub-task names.
        req_sub_task_match = REQUIRED_SUB_TASK_RE.match(message)
        if req_sub_task_match:
            names = None
            if req_sub_task_match.group(2) == global_data.CLI_DEST_NAME_PREFIX:
                names = sorted(registry.get_primary_task_names())
            else:
                dest_name = metavar_to_dest_name(req_sub_task_match.group(2))
                mt = registry.MAPPED_TASKS_BY_DEST_NAME.get(dest_name)
                if mt:
                    names = sorted(mt.sub_task_names())
            if names:
                name_list = ', '.join([f"'{name}'" for name in names])
                return f'{message} (choose from {name_list})'
        return message

    @staticmethod
    def _dump(method_name, *args, **kwargs):
        if global_data.DEBUG:
            log_message(f'argparse: {format_call_string(method_name, *args, **kwargs)})')

    @staticmethod
    def _abort(method_name, exc, *args, **kwargs):
        abort(f'argparse: {format_call_string(method_name, *args, **kwargs)})', exception=exc)

    @classmethod
    @contextmanager
    def _exceptions(cls):
        cls.raise_exceptions = True
        try:
            yield
        finally:
            cls.raise_exceptions = False


class ArgparseHelpFormatter(HelpFormatter):

    def __init__(self, parser: ArgumentParser):
        self.parser = parser

    def format_help(self) -> Text:
        return self.parser.format_help()


def _get_mapped_tasks() -> List[registry.MappedTask]:
    return sorted(filter(lambda m: m.name, registry.MAPPED_TASKS), key=lambda m: m.name)


@dataclass
class CommandLineData:
    """Results returned after parsing the command line."""
    # Parsed argument namespace.
    args: argparse.Namespace
    # Trailing argument list, if captured. Used by `alias` command.
    trailing_args: List[Text]
    # Chosen mapped task, based on primary command name.
    mapped_task: registry.MappedTask
    # Help formatter map used by `help` command.
    help_formatters: Dict[Text, HelpFormatter]


def _create_primary_parser(*args, **kwargs) -> ArgumentParser:
    parser = ArgumentParser(*args, **kwargs)
    if not registry.ToolOptions.disable_debug:
        parser.add_argument('-d', dest='DEBUG', action='store_true',
                            help='enable debug mode')
    if not registry.ToolOptions.disable_dry_run:
        parser.add_argument('-n', dest='DRY_RUN', action='store_true',
                            help='display actions without executing them')
    if not registry.ToolOptions.disable_verbose:
        parser.add_argument('-v', dest='VERBOSE', action='store_true',
                            help='display additional (verbose) messages')
    return parser


def _create_empty_namespace() -> argparse.Namespace:
    data = {}
    if not registry.ToolOptions.disable_debug:
        data['DEBUG'] = None
    if not registry.ToolOptions.disable_dry_run:
        data['DRY_RUN'] = None
    if not registry.ToolOptions.disable_verbose:
        data['VERBOSE'] = None
    return argparse.Namespace(**data)


class _CommandLineParser:

    def __init__(self,
                 cli_args: List[Text] = None,
                 prog: Text = None,
                 capture_trailing: bool = False):
        """
        Command line parser manager constructor.
        :param cli_args: command line argument list override
        :param prog: program name override
        :param capture_trailing: allow and capture trailing arguments if True
        """
        self.cli_args = cli_args if cli_args is not None else sys.argv
        self.prog = prog
        self.capture_trailing = capture_trailing
        self.parser: Optional[ArgumentParser] = None
        self.dest_name_preamble = (global_data.CLI_DEST_NAME_PREFIX +
                                   global_data.CLI_DEST_NAME_SEPARATOR)

    def parse(self, *args, **kwargs) -> CommandLineData:
        """

        :param args: positional arguments to pass along to ArgumentParser constructor
        :param kwargs:  keyword arguments to pass along to ArgumentParser constructor
        :return: parse results for command line
        """
        # Create top parser with global debug/verbose/dry-run options.
        self.parser = _create_primary_parser(*args, **kwargs, prog=self.prog)

        # Recursively build the parser tree under the primary sub-parser group.
        help_formatters = {make_dest_name(): ArgparseHelpFormatter(self.parser)}
        top_group = self.parser.add_subparsers(dest=global_data.CLI_DEST_NAME_PREFIX,
                                               metavar=global_data.CLI_DEST_NAME_PREFIX,
                                               required=True)
        for mt in _get_mapped_tasks():
            sub_parser = top_group.add_parser(mt.name, help=mt.help)
            self._prepare_parser_recursive(mt, sub_parser, help_formatters)

        # Parse the command line arguments.
        if self.capture_trailing:
            args, trailing_args = self.parser.parse_known_args(self.cli_args)
        else:
            args = self.parser.parse_args(self.cli_args)
            trailing_args: List[Text] = []

        # Get the most specific task name (longest length TASK.* name).
        task_dest = ''
        for dest in dir(args):
            if ((dest == global_data.CLI_DEST_NAME_PREFIX or
                 dest.startswith(self.dest_name_preamble)) and
                    len(dest) > len(task_dest)):
                task_dest = dest
        if not task_dest:
            raise RuntimeError(f'No {global_data.CLI_DEST_NAME_PREFIX}* member'
                               f' in command line arguments namespace: {args}')

        # Look up the mapped task using <dest>.<uppercase-name>.
        full_dest_name = append_dest_name(task_dest, getattr(args, task_dest))
        if full_dest_name not in registry.MAPPED_TASKS_BY_DEST_NAME:
            raise RuntimeError(f'''\
No mapped task was registered with the name: {full_dest_name}.
Parsed args: {args}
Known dests: {list(registry.MAPPED_TASKS_BY_DEST_NAME.keys())}
''')

        # Shouldn't have trailing arguments unless the specific command needs it.
        mapped_task = registry.MAPPED_TASKS_BY_DEST_NAME[full_dest_name]
        if trailing_args and not mapped_task.trailing_arguments:
            abort(f'Unexpected trailing arguments for command:',
                  ' '.join(mapped_task.get_full_command_names()))

        return CommandLineData(args, trailing_args, mapped_task, help_formatters)

    def _prepare_parser_recursive(self,
                                  mt: registry.MappedTask,
                                  parser: ArgumentParser,
                                  help_formatters: Dict[Text, HelpFormatter]):
        # The task runner must be able to format help text.
        help_formatters[mt.dest_name] = ArgparseHelpFormatter(parser)
        if mt.options:
            for flag_or_flags, option_data in mt.options.items():
                if isinstance(flag_or_flags, str):
                    parser.add_argument(flag_or_flags, **option_data)
                else:
                    parser.add_argument(*flag_or_flags, **option_data)
        if mt.arguments:
            for argument_data in mt.arguments:
                parser.add_argument(**argument_data)
        if mt.sub_tasks:
            sub_group = parser.add_subparsers(dest=mt.dest_name,
                                              metavar=mt.metavar,
                                              required=True)
            for sub_task in mt.sub_tasks:
                sub_parser = sub_group.add_parser(sub_task.name, help=sub_task.help)
                self._prepare_parser_recursive(sub_task, sub_parser, help_formatters)


def pre_parse_command_line(cli_args: List[Text] = None
                           ) -> Tuple[argparse.Namespace, List[Text]]:
    """
    Pre-parse the command line to get global options or to peek at command arguments.

    :param cli_args: argument list to pre-parse (overrides sys.argv)
    :return: (namespace, trailing-argument-list)
    """
    if cli_args is None:
        cli_args = sys.argv
    parser = _create_primary_parser()
    try:
        args, trailing_args = parser.parse_known_args(cli_args, raise_exceptions=True)
    except ArgumentParserError:
        return _create_empty_namespace(), []
    return args, trailing_args


def parse_command_line(cli_args: List[Text] = None,
                       name: Text = None,
                       description: Text = None,
                       capture_trailing: bool = False,
                       ) -> CommandLineData:
    """Set up command line parsers, parse, and return parsed command line data."""
    command_line_parser = _CommandLineParser(cli_args=cli_args,
                                             prog=name,
                                             capture_trailing=capture_trailing)
    return command_line_parser.parse(description=description)
