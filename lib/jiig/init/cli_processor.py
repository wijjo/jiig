"""
Command line argument parsing.
"""

from dataclasses import dataclass
from typing import Text, List, Optional

from jiig import cli, const, model
from jiig.util.alias_catalog import expand_alias_name, open_alias_catalog
from jiig.util.console import abort
from jiig.util.general import make_list

from .cli_preprocessor import CLIPreParseData


def _add_task_arguments_and_subcommands(command: cli.ParserCommand,
                                        registered_task: model.RegisteredTask):
    for opt in registered_task.opts:
        command.add_option(opt.name,
                           opt.description,
                           make_list(opt.flags),
                           is_boolean=opt.is_boolean,
                           cardinality=opt.cardinality,
                           default_value=opt.default_value,
                           choices=opt.choices)
    for arg in registered_task.args:
        command.add_positional_argument(arg.name,
                                        arg.description or '(no description)',
                                        cardinality=arg.cardinality,
                                        default_value=arg.default_value,
                                        choices=arg.choices)
    for sub_task_name, registered_sub_task in registered_task.sub_tasks.items():
        sub_command = command.add_sub_command(sub_task_name,
                                              registered_sub_task.description)
        _add_task_arguments_and_subcommands(sub_command, registered_sub_task)


@dataclass
class CLIParseData:
    data: object
    names: List[Text]
    trailing_arguments: Optional[List[Text]]


def initialize(configuration: model.ToolConfiguration,
               registered_tool: model.RegisteredTool,
               pre_results: CLIPreParseData,
               ) -> CLIParseData:
    """
    Parse the command line.

    :param configuration: tool configuration
    :param registered_tool: registered tool
    :param pre_results: preliminary command line parsing results
    :return: data loaded from the configuration file
    """
    # Create and initialize the parser driver.
    parser_driver = cli.get_parser_driver(
        configuration.tool_name,
        registered_tool.configuration.description,
        implementation=configuration.parser_implementation,
        disable_debug=configuration.disable_debug,
        disable_dry_run=configuration.disable_dry_run,
        disable_verbose=configuration.disable_verbose)
    root = parser_driver.initialize_parser()
    for task_name, registered_task in registered_tool.tasks.items():
        command = root.add_command(task_name, registered_task.description)
        _add_task_arguments_and_subcommands(command, registered_task)

    # Build the final arguments list, expanding an alias as required.
    if not pre_results.trailing_arguments:
        final_arguments = []
    elif not expand_alias_name(pre_results.trailing_arguments[0]):
        final_arguments = pre_results.trailing_arguments
    else:
        with open_alias_catalog(configuration.tool_name, const.DEFAULT_ALIASES_PATH) as catalog:
            alias = catalog.resolve_alias(pre_results.trailing_arguments[0])
            if not alias:
                abort(f'Alias "{pre_results.trailing_arguments[0]}" not found.')
            final_arguments = alias.command + pre_results.trailing_arguments[1:]

    parse_results = parser_driver.parse(final_arguments, capture_trailing=True)
    return CLIParseData(parse_results.data,
                        parse_results.names,
                        parse_results.trailing_arguments,
                        )
