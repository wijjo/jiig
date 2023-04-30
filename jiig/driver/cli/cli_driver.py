# Copyright (C) 2021-2023, Steven Cooper
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

"""Command line parser driver."""

from inspect import isclass
from typing import Sequence

from jiig.task import RuntimeTask, get_task_stack
from jiig.util.collections import make_list
from jiig.util.log import abort, log_message, log_error, ConsoleLogWriter
from jiig.util.text.grammar import pluralize

from ..driver import Driver, DriverPreliminaryAppData, DriverAppData
from ..driver_options import DriverOptions

from .cli_parser import Parser
from .cli_help import (
    CLIHelpProvider,
    CLIHelpProviderOptions,
)
from .cli_types import (
    CLIOptionArgument,
    CLIPositionalArgument,
    CLICommand,
)

CLI_HINT_OPTIONS = 'cli_options'
CLI_HINT_TRAILING = 'cli_trailing'


CLI_GLOBAL_OPTIONS = [
    CLIOptionArgument(
        'debug',
        'enable debug mode for additional diagnostics',
        ['--debug'],
        is_boolean=True,
    ),
    CLIOptionArgument(
        'dry_run',
        'display actions without executing them (dry run)',
        ['--dry-run'],
        is_boolean=True,
    ),
    CLIOptionArgument(
        'verbose',
        'display additional (verbose) messages',
        ['-v', '--verbose'],
        is_boolean=True,
    ),
    CLIOptionArgument(
        'pause',
        'pause before significant activity',
        ['--pause'],
        is_boolean=True,
    ),
    CLIOptionArgument(
        'keep_files',
        'keep (do not delete) temporary files',
        ['--keep-files'],
        is_boolean=True,
    ),
]


class CLIDriver(Driver):
    """
    Jiig driver for CLI.

    Note that this driver is stateful, and assumes a particular calling sequence.
    """
    def __init__(self,
                 name: str,
                 description: str,
                 options: DriverOptions = None,
                 ):
        """
        Jiig driver constructor.

        :param name: tool name
        :param description: tool description
        :param options: various driver options
        """
        super().__init__(name=name,
                         description=description,
                         options=options)
        self.cli_parser = Parser(self.options.top_task_dest_name)
        self.global_options = [
            global_option
            for global_option in CLI_GLOBAL_OPTIONS
            if global_option.name in options.global_option_names
        ]
        # Populated later.
        self.trailing_by_task: dict[str, str] = {}
        self.options_by_task: dict[str, dict[str, list[str]]] = {}

    def on_initialize_driver(self,
                             command_line_arguments: Sequence[str],
                             ) -> DriverPreliminaryAppData:
        """
        Driver initialization.

        :param command_line_arguments: command line argument list
        :return: preliminary argument list
        """
        data, additional_arguments = self.cli_parser.pre_parse(
            command_line_arguments,
            raise_exceptions=self.options.raise_exceptions,
            options=self.global_options,
        )
        return DriverPreliminaryAppData(data, additional_arguments)

    def on_initialize_application(self,
                                  arguments: list[str],
                                  root_task: RuntimeTask,
                                  ) -> DriverAppData:
        """
        Required arguments initialization call-back.

        NB: Slightly dishonest, because the returned data object may get updated
        with trailing arguments in on_initialize_tasks().

        :param arguments: argument list
        :param root_task: root task
        :return: driver application data
        """
        root_command = CLICommand(root_task.name,
                                  root_task.description,
                                  root_task.visibility)
        self._add_task_tree([], root_command, root_task)
        option_names = [option.name for option in root_command.options]
        for global_option in self.global_options:
            if global_option.name not in option_names:
                root_command.options.append(global_option)
        data, names, additional_arguments = self.cli_parser.parse(
            arguments,
            self.name,
            self.phase,
            root_command,
            capture_trailing=True,
            raise_exceptions=False,
        )
        if not names:
            abort(f'Program defines no tasks.')
        full_name = '.'.join(names)
        # Resolve task stack.
        task_stack = get_task_stack(root_task, names)
        # Inject trailing arguments into argument data object as needed.
        trailing_field_name = self.trailing_by_task.get(full_name)
        for field in task_stack[-1].fields:
            if field.name == trailing_field_name:
                if field.repeat is None:
                    abort(f'Field assigned to trailing arguments must repeat.',
                          task=task_stack[-1].name,
                          field=field.name)
                setattr(data, field.name, additional_arguments)
                break
        else:
            if additional_arguments:
                argument_word = pluralize(
                    "argument", additional_arguments)
                abort(f'Unexpected {argument_word} to command:', full_name)
        return DriverAppData(data, names, additional_arguments, task_stack)

    def on_provide_help(self,
                        root_task: RuntimeTask,
                        names: list[str],
                        show_hidden: bool):
        """
        Required override to provide help output.

        :param root_task: root task
        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        help_options = CLIHelpProviderOptions(
            top_task_label=self.options.top_task_label,
            sub_task_label=self.options.sub_task_label,
        )
        provider = CLIHelpProvider(self.name,
                                   self.description,
                                   root_task,
                                   self.options_by_task,
                                   self.global_options,
                                   self.trailing_by_task,
                                   help_options=help_options)
        text = provider.format_help(*names, show_hidden=show_hidden)
        if text:
            log_message(text)

    def get_log_writer(self) -> ConsoleLogWriter:
        """
        Required override to provide a log writer.

        :return: log writer
        """
        return ConsoleLogWriter()

    def _add_task_tree(self,
                       names: list[str],
                       command: CLICommand,
                       task: RuntimeTask,
                       ):
        full_name = '.'.join(names)
        if task.driver_hints:
            option_hints = task.driver_hints.get(CLI_HINT_OPTIONS)
            if option_hints:
                if isinstance(option_hints, dict):
                    for field_name, raw_flags in option_hints.items():
                        flag_list = make_list(raw_flags, sep=',')
                        if flag_list:
                            if full_name not in self.options_by_task:
                                self.options_by_task[full_name] = {}
                            self.options_by_task[full_name][field_name] = flag_list
                else:
                    log_error(f'hints[{CLI_HINT_OPTIONS}] is not a dictionary.',
                              option_hints)
            trailing_field = task.driver_hints.get(CLI_HINT_TRAILING)
            if trailing_field:
                self.trailing_by_task[full_name] = trailing_field
        option_names: set[str] = set()
        options_by_field = self.options_by_task.get(full_name, {})
        for field in task.fields:
            if field.name in options_by_field:
                is_boolean = isclass(field.element_type) and issubclass(field.element_type, bool)
                option = CLIOptionArgument(
                    field.name,
                    field.description,
                    options_by_field[field.name],
                    is_boolean=is_boolean,
                    repeat=field.repeat,
                    default=field.default,
                    choices=field.choices,
                )
                command.options.append(option)
                option_names.add(field.name)
        trailing_field_name = self.trailing_by_task.get(full_name)
        for field in task.fields:
            if field.name not in options_by_field:
                # Trailing argument capture is handled separately.
                if field.name != trailing_field_name:
                    positional = CLIPositionalArgument(
                        field.name,
                        field.description or '(no description)',
                        repeat=field.repeat,
                        default=field.default,
                        choices=field.choices,
                    )
                    command.positionals.append(positional)
        for sub_task in task.sub_tasks:
            sub_command = CLICommand(sub_task.name,
                                     sub_task.description,
                                     sub_task.visibility)
            command.sub_commands.append(sub_command)
            self._add_task_tree(names + [sub_task.name], sub_command, sub_task)
