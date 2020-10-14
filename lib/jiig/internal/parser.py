"""
Argument parsing support.
"""

import argparse
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, List, Text, Dict, Sequence, Tuple, Iterator

from jiig.internal import global_data, tool_options
from jiig.internal.help_formatter import HelpFormatter, HelpSubTaskData
from jiig.internal.mapped_task import MappedTask
from jiig.internal.registry import get_sorted_named_mapped_tasks, get_mapped_task_by_dest_name, \
    get_tool_tasks
from jiig.utility.cli import append_dest_name, make_dest_name
from jiig.utility.console import abort, log_message
from jiig.utility.python import format_call_string

# Expose Namespace, since it's pretty generic, so that other modules don't need
# to know about argparse.
Namespace = argparse.Namespace

# Expression for making a friendlier error message for missing sub-task.
REQUIRED_SUB_TASK_RE = re.compile(fr'^(.* required: )' 
                                  fr'({global_data.cli_dest_name_prefix}'
                                  fr'|[A-Z_]+_{global_data.cli_metavar_suffix})$')
HELP_BLOCK_HEADER_RE = re.compile(r'^(\w+) arguments:$')
POSITIONAL_ARGUMENTS_MARKER = '{TASKS}'


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
        # Remove any keywords that argparse does not handle.
        if 'common_footnotes' in kwargs:
            del kwargs['common_footnotes']
        if global_data.debug:
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
        if global_data.debug:
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
        if global_data.debug:
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
        message = message.replace(POSITIONAL_ARGUMENTS_MARKER, 'TASK')
        if REQUIRED_SUB_TASK_RE.match(message):
            prog_words = self.prog.split()
            if len(prog_words) == 1:
                label = 'TASK'
                help_command = f'{prog_words[0]} help'
            else:
                label = 'SUB_TASK'
                help_command = f'{" ".join(prog_words[:-1])} help {prog_words[-1]}'
            sys.stderr.write(f'"{self.prog}" requires a {label} argument.')
            sys.stderr.write(os.linesep)
            sys.stderr.write(f'See "{help_command}" for more information.')
            sys.stderr.write(os.linesep)
            sys.exit(0)
        super().error(message)

    @staticmethod
    def _dump(method_name, *args, **kwargs):
        if global_data.debug:
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


@dataclass
class CommandLineData:
    """Results returned after parsing the command line."""
    # Parsed argument namespace.
    args: argparse.Namespace
    # Trailing argument list, if captured. Used by `alias` command.
    trailing_args: List[Text]
    # Chosen mapped task, based on primary command name.
    mapped_task: MappedTask
    # Help formatter map used by `help` command.
    help_formatters: Dict[Text, HelpFormatter]


def _create_primary_parser(*args, **kwargs) -> ArgumentParser:
    parser = ArgumentParser(*args, **kwargs)
    if not tool_options.disable_debug:
        parser.add_argument('--debug', dest='DEBUG', action='store_true',
                            help='enable debug mode')
    if not tool_options.disable_dry_run:
        parser.add_argument('--dry-run', dest='DRY_RUN', action='store_true',
                            help='display actions without executing (dry run)')
    if not tool_options.disable_verbose:
        parser.add_argument('-v', dest='VERBOSE', action='store_true',
                            help='display additional (verbose) messages')
    return parser


def _create_empty_namespace() -> argparse.Namespace:
    data = {}
    if not tool_options.disable_debug:
        data['DEBUG'] = None
    if not tool_options.disable_dry_run:
        data['DRY_RUN'] = None
    if not tool_options.disable_verbose:
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
        self.dest_name_preamble = (global_data.cli_dest_name_prefix +
                                   global_data.cli_dest_name_separator)

    @staticmethod
    def _get_help_sub_task_data(mapped_tasks: Iterator[MappedTask]) -> List[HelpSubTaskData]:
        return [
            HelpSubTaskData(mapped_task.name, mapped_task.help_visibility, mapped_task.help)
            for mapped_task in sorted(mapped_tasks, key=lambda t: t.name)
        ]

    def parse(self, *args, **kwargs) -> CommandLineData:
        """
        Parse the command line.

        :param args: positional arguments to pass along to ArgumentParser constructor
        :param kwargs:  keyword arguments to pass along to ArgumentParser constructor
        :return: parse results for command line
        """
        # Create top parser with global debug/verbose/dry-run options.
        self.parser = _create_primary_parser(*args, **kwargs,
                                             prog=self.prog,
                                             add_help=False)

        # Recursively build the parser tree under the primary sub-parser group.
        top_formatter = HelpFormatter(
            'TASK',
            [tool_options.name],
            tool_options.description,
            sub_tasks=self._get_help_sub_task_data(get_tool_tasks(include_hidden=True)),
            notes=tool_options.notes,
            footnote_dictionaries=[tool_options.common_footnotes])
        help_formatters = {make_dest_name(): top_formatter}
        top_group = self.parser.add_subparsers(dest=global_data.cli_dest_name_prefix,
                                               metavar=POSITIONAL_ARGUMENTS_MARKER,
                                               required=True)
        for mapped_task in get_sorted_named_mapped_tasks():
            sub_parser = top_group.add_parser(mapped_task.name,
                                              help=mapped_task.help,
                                              add_help=False)
            self._prepare_parser_recursive(mapped_task,
                                           sub_parser,
                                           [self.prog],
                                           help_formatters)

        # Parse the command line arguments.
        if self.capture_trailing:
            args, trailing_args = self.parser.parse_known_args(self.cli_args)
        else:
            args = self.parser.parse_args(self.cli_args)
            trailing_args: List[Text] = []

        # Get the most specific task name (longest length TASK.* name).
        task_dest = ''
        for dest in dir(args):
            if ((dest == global_data.cli_dest_name_prefix or
                 dest.startswith(self.dest_name_preamble)) and
                    len(dest) > len(task_dest)):
                task_dest = dest
        if not task_dest:
            raise RuntimeError(f'No {global_data.cli_dest_name_prefix}* member'
                               f' in command line arguments namespace: {args}')

        # Look up the mapped task using <dest>.<uppercase-name>.
        full_dest_name = append_dest_name(task_dest, getattr(args, task_dest))
        mapped_task = get_mapped_task_by_dest_name(full_dest_name)
        if not mapped_task:
            raise RuntimeError(f'No mapped task was registered with the name: {full_dest_name}.')

        # Shouldn't have trailing arguments unless the specific command needs it.
        mapped_task = get_mapped_task_by_dest_name(full_dest_name)
        if trailing_args and not mapped_task.trailing_arguments:
            abort(f'Unexpected trailing arguments for command:',
                  ' '.join(mapped_task.get_full_command_names()))

        return CommandLineData(args, trailing_args, mapped_task, help_formatters)

    def _prepare_parser_recursive(self,
                                  mapped_task: MappedTask,
                                  parser: ArgumentParser,
                                  command_names: List[Text],
                                  help_formatters: Dict[Text, HelpFormatter]):
        sub_command_names = command_names + [mapped_task.name]
        help_formatters[mapped_task.dest_name] = HelpFormatter(
            'SUB_TASK',
            sub_command_names,
            mapped_task.description,
            sub_tasks=self._get_help_sub_task_data(mapped_task.sub_tasks),
            options=mapped_task.options,
            arguments=mapped_task.arguments,
            notes=mapped_task.notes,
            footnote_dictionaries=[tool_options.common_footnotes, mapped_task.footnotes]
        )
        for flags, option_data in mapped_task.options.items():
            parser.add_argument(*flags, **option_data)
        for argument_data in mapped_task.arguments:
            parser.add_argument(**argument_data)
        if mapped_task.sub_tasks:
            sub_group = parser.add_subparsers(dest=mapped_task.dest_name,
                                              metavar=POSITIONAL_ARGUMENTS_MARKER,
                                              required=True)
            for sub_task in mapped_task.sub_tasks:
                sub_parser = sub_group.add_parser(sub_task.name,
                                                  help=sub_task.help,
                                                  add_help=False)
                self._prepare_parser_recursive(sub_task,
                                               sub_parser,
                                               sub_command_names,
                                               help_formatters)


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
