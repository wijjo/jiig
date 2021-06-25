"""Command line parser driver."""

import os
from dataclasses import dataclass
from inspect import isclass
from typing import Text, Sequence, List, Optional, Type

from jiig.util.alias_catalog import is_alias_name, open_alias_catalog
from jiig.util.log import abort, ConsoleLogWriter
from jiig.util.general import make_list, plural
from jiig.util.process import shell_command_string
from jiig.util.python import import_module_path

from ..driver import Driver, IMPLEMENTATION_CLASS_NAME
from ..driver_options import DriverOptions
from ..driver_task import DriverTask
from ..driver_types import DriverInitializationData, DriverApplicationData

from .cli_command import CLICommand
from .cli_help import CLIHelpProvider, CLIHelpProviderOptions
from .cli_hints import CLI_HINT_FLAGS, CLI_HINT_TRAILING
from .cli_implementation import CLIImplementation
from .cli_types import CLIOptions, CLIOption
from .global_options import GLOBAL_OPTIONS


@dataclass
class CLIInitializationData(DriverInitializationData):
    cli_implementation: CLIImplementation


@dataclass
class CLIApplicationData(DriverApplicationData):
    # Command names.
    names: List[Text]
    # Trailing arguments, if requested, following any options.
    trailing_arguments: Optional[List[Text]]


class CLIDriver(Driver):
    """
    Jiig driver for CLI.

    Note that this driver is stateful, and assumes a particular calling sequence.
    """
    supported_hints: List[Text] = [CLI_HINT_FLAGS, CLI_HINT_TRAILING]

    def __init__(self,
                 name: Text,
                 description: Text,
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

    def on_initialize_driver(self,
                             command_line_arguments: Sequence[Text],
                             ) -> CLIInitializationData:
        """
        Driver initialization.

        :param command_line_arguments: command line argument list
        :return: driver initialization data
        """
        variant = self.options.variant
        if variant is None:
            variant = 'argparse'
        module_path = os.path.join(os.path.dirname(__file__), 'impl', variant + '.py')
        parser_module = import_module_path(module_path)
        implementation_class: Type[CLIImplementation] = getattr(
            parser_module, IMPLEMENTATION_CLASS_NAME, None)
        if implementation_class is None:
            raise RuntimeError(f'{parser_module.__name__} missing'
                               f' {IMPLEMENTATION_CLASS_NAME} class.')
        cli_implementation = implementation_class()
        cli_implementation.top_task_dest_name = self.options.top_task_dest_name
        options = CLIOptions(raise_exceptions=self.options.raise_exceptions,
                             global_options=self._get_supported_global_options())
        pre_parse_results = cli_implementation.on_pre_parse(command_line_arguments, options)
        # Scrape up enabled global option names from parse result data attributes.
        self.enabled_global_options: List[Text] = [
            option.name for option in GLOBAL_OPTIONS
            if getattr(pre_parse_results.data, option.dest, False)
        ]
        # Expand alias as needed to produce final argument list.
        expanded_arguments = _expand_alias_as_needed(
            self.name, pre_parse_results.trailing_arguments)
        return CLIInitializationData(expanded_arguments, cli_implementation)

    def _get_supported_global_options(self) -> List[CLIOption]:
        return [CLIOption(option.name, option.description, option.flags, is_boolean=True)
                for option in GLOBAL_OPTIONS
                if option.name in self.options.supported_global_options]

    def on_initialize_application(self,
                                  initialization_data: CLIInitializationData,
                                  root_task: DriverTask,
                                  ) -> CLIApplicationData:
        """
        Required application initialization call-back.

        :param initialization_data: driver initialization data
        :param root_task: root task
        :return: driver application data
        """

        root_command = CLICommand(root_task.name, root_task.description)
        _add_task_fields(root_command, root_task)
        for sub_task in root_task.sub_tasks:
            command = root_command.add_sub_command(sub_task.name, sub_task.description)
            _add_task_fields_and_subcommands(command, sub_task)

        options = CLIOptions(capture_trailing=True,
                             raise_exceptions=False,
                             global_options=self._get_supported_global_options())
        parse_results = initialization_data.cli_implementation.on_parse(
            initialization_data.final_arguments,
            self.name,
            self.phase,
            root_command,
            options,
        )

        # Make sure global options have values, even if disabled.
        for global_option in GLOBAL_OPTIONS:
            if global_option.name not in self.options.supported_global_options:
                setattr(parse_results.data, global_option.dest, False)

        # Resolve the task stack.
        try:
            task_stack = root_task.resolve_task_stack(parse_results.names)
            if task_stack is None:
                abort(f'Failed to resolve command.', ' '.join(parse_results.names))
            for field in task_stack[-1].fields:
                receives_trailing_arguments = bool(field.hints.get(CLI_HINT_TRAILING))
                if receives_trailing_arguments:
                    # Inject trailing arguments attribute into data object.
                    setattr(parse_results.data, field.name, parse_results.trailing_arguments)
                    break
            else:
                if parse_results.trailing_arguments:
                    argument_word = plural("argument", parse_results.trailing_arguments)
                    abort(f'Unexpected {argument_word} to command:',
                          shell_command_string(self.name, *initialization_data.final_arguments))
            return CLIApplicationData(task_stack,
                                      parse_results.data,
                                      parse_results.names,
                                      parse_results.trailing_arguments)
        except ValueError as exc:
            abort(str(exc))

    def on_provide_help(self,
                        root_task: DriverTask,
                        names: List[Text],
                        show_hidden: bool):
        """
        Required override to provide help output.

        :param root_task: root task
        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        options = CLIHelpProviderOptions(
            top_task_label=self.options.top_task_label,
            sub_task_label=self.options.sub_task_label,
            supported_global_options=self.options.supported_global_options,
        )
        provider = CLIHelpProvider(self.name,
                                   self.description,
                                   root_task,
                                   options=options)
        text = provider.format_help(*names, show_hidden=show_hidden)
        if text:
            print(text)

    def get_log_writer(self) -> ConsoleLogWriter:
        """
        Required override to provide a log writer.

        :return: log writer
        """
        return ConsoleLogWriter()


def _add_task_fields(command: CLICommand,
                     task: DriverTask):
    for field in task.fields:
        flags = field.hints.get(CLI_HINT_FLAGS)
        if flags:
            is_boolean = isclass(field.element_type) and issubclass(field.element_type, bool)
            command.add_option(field.name,
                               field.description,
                               make_list(flags),
                               is_boolean=is_boolean,
                               repeat=field.repeat,
                               default=field.default,
                               choices=field.choices)
    for field in task.fields:
        flags = field.hints.get(CLI_HINT_FLAGS)
        if not flags:
            # Trailing argument capture is handled separately.
            if not bool(field.hints.get(CLI_HINT_TRAILING)):
                command.add_positional(field.name,
                                       field.description or '(no description)',
                                       repeat=field.repeat,
                                       default=field.default,
                                       choices=field.choices)


def _add_task_fields_and_subcommands(command: CLICommand,
                                     task: DriverTask):
    _add_task_fields(command, task)
    for sub_sub_task in task.sub_tasks:
        sub_command = command.add_sub_command(sub_sub_task.name,
                                              sub_sub_task.description)
        _add_task_fields_and_subcommands(sub_command, sub_sub_task)


def _expand_alias_as_needed(tool_name: Text, trailing_arguments: List[Text]) -> List[Text]:
    # Build the final arguments list, expanding an alias as required.
    if not trailing_arguments:
        final_arguments: List[Text] = []
    elif not is_alias_name(trailing_arguments[0]):
        final_arguments = trailing_arguments
    else:
        with open_alias_catalog(tool_name) as catalog:
            alias = catalog.get_alias(trailing_arguments[0])
            if not alias:
                abort(f'Alias "{trailing_arguments[0]}" not found.')
            final_arguments = alias.command + trailing_arguments[1:]
    return final_arguments
