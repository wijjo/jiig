"""
Command line argument parsing.
"""

from dataclasses import dataclass
from typing import Text, List, Optional

from jiig.constants import ALIASES_PATH
from jiig.cli_parsing import ParserCommand, get_parser_driver
from jiig.registration.registered_tasks import RegisteredTask
from jiig.registration.registered_tools import RegisteredTool
from jiig.utility.alias_catalog import expand_alias_name, open_alias_catalog
from jiig.utility.console import abort
from jiig.utility.general import make_list

from .cli_preprocessor import CLIPreResults
from .execution_data import ExecutionData


def _add_task_arguments_and_subcommands(command: ParserCommand,
                                        registered_task: RegisteredTask):
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
class CLIResults:
    data: object
    names: List[Text]
    trailing_arguments: Optional[List[Text]]
    pip_packages: List[Text]


def initialize(exec_data: ExecutionData,
               registered_tool: RegisteredTool,
               pre_results: CLIPreResults,
               ) -> CLIResults:
    """
    Parse the command line.

    :param exec_data: script paths and command line arguments data
    :param registered_tool: registered tool
    :param pre_results: preliminary command line parsing results
    :return: data loaded from the configuration file
    """
    # Create and initialize the parser driver.
    parser_driver = get_parser_driver(
        registered_tool.tool_name,
        registered_tool.description,
        implementation=exec_data.parser_implementation,
        disable_debug=registered_tool.options.disable_debug,
        disable_dry_run=registered_tool.options.disable_dry_run,
        disable_verbose=registered_tool.options.disable_verbose)
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
        with open_alias_catalog(registered_tool.tool_name, ALIASES_PATH) as catalog:
            alias = catalog.resolve_alias(pre_results.trailing_arguments[0])
            if not alias:
                abort(f'Alias "{pre_results.trailing_arguments[0]}" not found.')
            final_arguments = alias.command + pre_results.trailing_arguments[1:]

    parse_results = parser_driver.parse(final_arguments, capture_trailing=True)
    return CLIResults(parse_results.data,
                      parse_results.names,
                      parse_results.trailing_arguments,
                      registered_tool.get_pip_packages(*parse_results.names),
                      )
