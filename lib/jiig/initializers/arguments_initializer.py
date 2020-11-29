"""
Command line argument parsing.
"""

from dataclasses import dataclass
from typing import List, Text

from jiig.cli_parse import ParserCommand, CommandLineParserDriver, get_parser_driver
from jiig.registry import RegisteredTask
from jiig.utility.alias_catalog import expand_alias_name, open_alias_catalog
from jiig.utility.console import abort
from jiig.utility.general import format_exception, make_list

from .parameters_initializer import ParameterData
from .tool_initializer import ToolData


@dataclass
class ArgumentData:
    data: object
    names: List[Text]
    trailing_arguments: List[Text]
    registered_task: RegisteredTask


def _prepare_arguments(registered_task: RegisteredTask, args_in: object) -> object:
    # Convert argument data.
    class _PreparedArguments:
        pass
    args_out = _PreparedArguments()
    exception_messages: List[Text] = []
    for argument in registered_task.arguments:
        if hasattr(args_in, argument.name):
            value = getattr(args_in, argument.name)
            adapter_name = '???'
            try:
                # Call all adapters to validate and convert as appropriate.
                for adapter in argument.adapters:
                    adapter_name = adapter.__name__
                    value = adapter(value)
                setattr(args_out, argument.name, value)
            except (TypeError, ValueError) as exc:
                exception_messages.append(
                    format_exception(exc,
                                     label=f'{argument.name}:{adapter_name}',
                                     skip_stack_levels=1))
    if exception_messages:
        plural = 's' if len(exception_messages) > 1 else ''
        abort(f'Task "{registered_task.name}" argument processing failure{plural}:',
              *exception_messages)
    return args_out


def _add_task_arguments_and_subcommands(command: ParserCommand,
                                        registered_task: RegisteredTask):
    for argument in registered_task.arguments:
        if argument.flags:
            command.add_option(argument.name,
                               argument.description or '(no description)',
                               make_list(argument.flags),
                               is_boolean=argument.is_boolean,
                               cardinality=argument.cardinality,
                               default_value=argument.default_value,
                               choices=argument.choices)
        else:
            command.add_positional_argument(argument.name,
                                            argument.description or '(no description)',
                                            cardinality=argument.cardinality,
                                            default_value=argument.default_value,
                                            choices=argument.choices)
    if registered_task.sub_tasks:
        for sub_task in registered_task.sub_tasks:
            sub_command = command.add_sub_command(
                sub_task.name, sub_task.description or '(no description)')
            _add_task_arguments_and_subcommands(sub_command, sub_task)


def _initialize_driver_tasks(parser_driver: CommandLineParserDriver,
                             registered_tasks: List[RegisteredTask],
                             ):
    # If registered_tasks is None - initializing for pre-parsing, not full parsing.
    if registered_tasks is not None:
        root = parser_driver.initialize_parser()
        for registered_task in registered_tasks:
            command = root.add_command(registered_task.name,
                                       registered_task.description or '(no description)')
            _add_task_arguments_and_subcommands(command, registered_task)
    return parser_driver


def initialize(param_data: ParameterData, tool_data: ToolData) -> ArgumentData:
    """
    Parse the command line.

    :param param_data: data from preliminary command line processing
    :param tool_data: data from the task registry
    :return: data loaded from the configuration file
    """
    parser_driver = get_parser_driver(tool_data.name,
                                      tool_data.description,
                                      implementation=param_data.parser_implementation,
                                      disable_debug=tool_data.disable_debug,
                                      disable_dry_run=tool_data.disable_dry_run,
                                      disable_verbose=tool_data.disable_verbose)
    _initialize_driver_tasks(parser_driver, tool_data.all_tasks)

    # Build the final arguments list, expanding an alias as required.
    if not param_data.trailing_arguments:
        final_arguments = []
    elif not expand_alias_name(param_data.trailing_arguments[0]):
        final_arguments = param_data.trailing_arguments
    else:
        with open_alias_catalog(tool_data.name, param_data.aliases_path) as catalog:
            alias = catalog.resolve_alias(param_data.trailing_arguments[0])
            if not alias:
                abort(f'Alias "{param_data.trailing_arguments[0]}" not found.')
            final_arguments = alias.command + param_data.trailing_arguments[1:]

    parse_results = parser_driver.parse(final_arguments,
                                        capture_trailing=tool_data.capture_trailing)

    # Get the registered task for the command line.
    full_name = param_data.full_name_separator.join(parse_results.names)
    registered_task = tool_data.tasks_by_name.get(full_name)
    if not registered_task:
        abort(f'No task was registered with the name "{full_name}".')
    # Shouldn't have trailing arguments unless the specific command needs it.
    if parse_results.trailing_arguments and not registered_task.receive_trailing_arguments:
        abort(f'Unexpected trailing arguments for command:', registered_task.name)
    data = _prepare_arguments(registered_task, parse_results.data)
    return ArgumentData(data,
                        parse_results.names,
                        parse_results.trailing_arguments,
                        registered_task)
