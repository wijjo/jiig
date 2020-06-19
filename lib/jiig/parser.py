import argparse
from typing import Optional, List, Text, Dict

from . import constants
from .task import MappedTask, MAPPED_TASKS, MAPPED_TASKS_BY_DEST_NAME
from .utility import append_dest_name, make_dest_name
from .runner import HelpFormatter

# Expose Namespace, since it's pretty generic, so that other modules don't need
# to know about argparse.
Namespace = argparse.Namespace


class ArgparseHelpFormatter(HelpFormatter):

    def __init__(self, parser: argparse.ArgumentParser):
        self.parser = parser

    def format_help(self) -> Text:
        return self.parser.format_help()


class CommandLineParser:

    def __init__(self):
        self.parser: Optional[argparse.ArgumentParser] = None
        self.mapped_tasks: List[MappedTask] = []
        self.args = None
        self.mapped_task: Optional[MappedTask] = None
        self.help_formatters: Dict[Text, HelpFormatter] = {}
        self.dest_name_preamble = (constants.Jiig.cli_dest_name_prefix +
                                   constants.Jiig.cli_dest_name_separator)

    def parse(self):
        self.parser = argparse.ArgumentParser(description='Execute application build/run tasks.')
        self.help_formatters[make_dest_name()] = ArgparseHelpFormatter(self.parser)
        self.parser.add_argument('-d', dest='DEBUG', action='store_true',
                                 help='enable debug mode')
        self.parser.add_argument('-v', dest='VERBOSE', action='store_true',
                                 help='display additional (verbose) messages')
        self.parser.add_argument('-n', dest='DRY_RUN', action='store_true',
                                 help='display actions without executing them')
        top_sub_group = self.parser.add_subparsers(dest=constants.Jiig.cli_dest_name_prefix,
                                                   metavar=constants.Jiig.cli_dest_name_prefix,
                                                   required=True)
        # Recursively build the parser tree.
        for mt in sorted(filter(lambda m: m.name, MAPPED_TASKS), key=lambda m: m.name):
            top_sub_parser = top_sub_group.add_parser(mt.name,
                                                      help=mt.help,
                                                      description=mt.description)
            self._prepare_parser_recursive(mt, top_sub_parser)
        # Parse the command line arguments.
        self.args = self.parser.parse_args()
        # Get the most specific task name (longest length TASK.* name).
        task_dest = ''
        for dest in dir(self.args):
            if ((dest == constants.Jiig.cli_dest_name_prefix or
                 dest.startswith(self.dest_name_preamble)) and
                    len(dest) > len(task_dest)):
                task_dest = dest
        if not task_dest:
            raise RuntimeError(f'No {constants.Jiig.cli_dest_name_prefix}* member'
                               f' in command line arguments namespace: {self.args}')
        # Look up the mapped task using <dest>.<uppercase-name>.
        full_dest_name = append_dest_name(task_dest, getattr(self.args, task_dest))
        if full_dest_name not in MAPPED_TASKS_BY_DEST_NAME:
            raise RuntimeError(f'''\
No mapped task was registered with the name: {full_dest_name}.
Parsed args: {self.args}
Known dests: {list(MAPPED_TASKS_BY_DEST_NAME.keys())}
''')
        self.mapped_task = MAPPED_TASKS_BY_DEST_NAME[full_dest_name]

    def _prepare_parser_recursive(self, mt: MappedTask, parser: argparse.ArgumentParser):
        # The task runner must be able to format help text.
        self.help_formatters[mt.dest_name] = ArgparseHelpFormatter(parser)
        self.mapped_tasks.append(mt)
        if mt.options:
            for flag, option_data in mt.options.items():
                parser.add_argument(flag, **option_data)
        if mt.arguments:
            for argument_data in mt.arguments:
                parser.add_argument(**argument_data)
        if mt.sub_tasks:
            sub_group = parser.add_subparsers(dest=mt.dest_name,
                                              metavar=mt.metavar,
                                              required=True)
            for sub_task in mt.sub_tasks:
                sub_parser = sub_group.add_parser(sub_task.name,
                                                  help=sub_task.help,
                                                  description=sub_task.description)
                self._prepare_parser_recursive(sub_task, sub_parser)
