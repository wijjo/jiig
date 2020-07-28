import argparse
import sys
from dataclasses import dataclass
from typing import Optional, List, Text, Dict

from . import constants
from .registry import MappedTask, MAPPED_TASKS, MAPPED_TASKS_BY_DEST_NAME
from .task_runner import HelpFormatter
from .utility import append_dest_name, make_dest_name, log_message, abort, format_call_string

# Expose Namespace, since it's pretty generic, so that other modules don't need
# to know about argparse.
Namespace = argparse.Namespace


class ArgparseHelpFormatter(HelpFormatter):

    def __init__(self, parser: argparse.ArgumentParser):
        self.parser = parser

    def format_help(self) -> Text:
        return self.parser.format_help()


class ArgumentParser(argparse.ArgumentParser):
    """Wrap a few functions for debug output."""

    @staticmethod
    def _dump(method_name, args, kwargs):
        if constants.DEBUG:
            log_message(f'argparse: {format_call_string(method_name, *args, **kwargs)})')

    @staticmethod
    def _abort(method_name, exc, args, kwargs):
        abort(f'argparse: {format_call_string(method_name, *args, **kwargs)})', exception=exc)

    def __init__(self, *args, **kwargs):
        self._dump('ArgumentParser', args, kwargs)
        try:
            super().__init__(*args, **kwargs)
        except Exception as exc:
            self._abort('ArgumentParser', exc, args, kwargs)

    def add_subparsers(self, *args, **kwargs):
        self._dump('add_subparsers', args, kwargs)
        try:
            return super().add_subparsers(*args, **kwargs)
        except Exception as exc:
            self._abort('add_subparsers', exc, args, kwargs)

    def add_argument(self, *args, **kwargs):
        if constants.DEBUG:
            self._dump('add_argument', args, kwargs)
        try:
            return super().add_argument(*args, **kwargs)
        except Exception as exc:
            self._abort('add_argument', exc, args, kwargs)


def _add_global_args(parser: argparse.ArgumentParser):
    parser.add_argument('-d', dest='DEBUG', action='store_true',
                        help='enable debug mode')
    parser.add_argument('-v', dest='VERBOSE', action='store_true',
                        help='display additional (verbose) messages')
    parser.add_argument('-n', dest='DRY_RUN', action='store_true',
                        help='display actions without executing them')


def pre_parse_global_args() -> argparse.Namespace:
    """Extract just the global option args for various run modes."""
    parser = argparse.ArgumentParser()
    _add_global_args(parser)
    return parser.parse_known_args()[0]


@dataclass
class CommandLineData:
    """Results returned after parsing the command line."""
    args: argparse.Namespace
    mapped_task: MappedTask
    help_formatters: Dict[Text, HelpFormatter]


class CommandLineParser:
    """Performs command line argument parsing for a Jiig application."""

    def __init__(self, cli_args: List[Text] = None, prog: Text = None):
        self.cli_args = cli_args if cli_args is not None else sys.argv
        self.prog = prog
        self.parser: Optional[argparse.ArgumentParser] = None
        self.mapped_tasks: List[MappedTask] = []
        self.dest_name_preamble = (constants.CLI_DEST_NAME_PREFIX +
                                   constants.CLI_DEST_NAME_SEPARATOR)

    def parse(self, *args, **kwargs) -> CommandLineData:
        """
        Build argparse parser and parse the command line.

        All ArgumentParser positional and keyword arguments may be provided.
        """
        self.parser = ArgumentParser(*args, **kwargs, prog=self.prog)
        # Add global debug/verbose/dry-run option args.
        _add_global_args(self.parser)
        # Container group for top level commands.
        top_sub_group = self.parser.add_subparsers(dest=constants.CLI_DEST_NAME_PREFIX,
                                                   metavar=constants.CLI_DEST_NAME_PREFIX,
                                                   required=True)
        # Recursively build the parser tree.
        help_formatters = {make_dest_name(): ArgparseHelpFormatter(self.parser)}
        for mt in sorted(filter(lambda m: m.name, MAPPED_TASKS), key=lambda m: m.name):
            top_sub_parser = top_sub_group.add_parser(mt.name, help=mt.help)
            self._prepare_parser_recursive(mt, top_sub_parser, help_formatters)
        # Parse the command line arguments.
        args = self.parser.parse_args(self.cli_args)
        # Get the most specific task name (longest length TASK.* name).
        task_dest = ''
        for dest in dir(args):
            if ((dest == constants.CLI_DEST_NAME_PREFIX or
                 dest.startswith(self.dest_name_preamble)) and
                    len(dest) > len(task_dest)):
                task_dest = dest
        if not task_dest:
            raise RuntimeError(f'No {constants.CLI_DEST_NAME_PREFIX}* member'
                               f' in command line arguments namespace: {args}')
        # Look up the mapped task using <dest>.<uppercase-name>.
        full_dest_name = append_dest_name(task_dest, getattr(args, task_dest))
        if full_dest_name not in MAPPED_TASKS_BY_DEST_NAME:
            raise RuntimeError(f'''\
No mapped task was registered with the name: {full_dest_name}.
Parsed args: {args}
Known dests: {list(MAPPED_TASKS_BY_DEST_NAME.keys())}
''')
        return CommandLineData(args,
                               MAPPED_TASKS_BY_DEST_NAME[full_dest_name],
                               help_formatters)

    def _prepare_parser_recursive(self,
                                  mt: MappedTask,
                                  parser: argparse.ArgumentParser,
                                  help_formatters: Dict[Text, HelpFormatter]):
        # The task runner must be able to format help text.
        help_formatters[mt.dest_name] = ArgparseHelpFormatter(parser)
        self.mapped_tasks.append(mt)
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
