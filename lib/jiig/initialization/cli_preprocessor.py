"""
Global option initialization using command line pre-processing.
"""

from dataclasses import dataclass
from typing import Text, List

from jiig.cli_parsing import get_parser_driver
from ..registration.registered_tools import RegisteredTool

from .execution_data import ExecutionData


@dataclass
class CLIPreResults:
    """Preliminary results from pre-parsed command line."""
    trailing_arguments: List[Text]
    debug: bool = False
    dry_run: bool = False
    verbose: bool = False


def initialize(exec_data: ExecutionData,
               registered_tool: RegisteredTool,
               ) -> CLIPreResults:
    """
    Initialize global options based on pre-parsed command line.

    :param exec_data: script paths and command line arguments data
    :param registered_tool: registered tool
    :return: pre-processed command line data
    """
    # Get the raw arguments, filtering out '--', if inserted before trailing arguments
    # after restarting in the virtual environment.
    if exec_data.cli_args and exec_data.cli_args[0] == '--':
        raw_arguments = exec_data.cli_args[1:]
    else:
        raw_arguments = exec_data.cli_args

    # Pre-parse raw arguments to get top level options and trailing arguments.
    parser_driver = get_parser_driver(
        registered_tool.tool_name,
        'pre-processing',
        implementation=exec_data.parser_implementation,
        disable_debug=registered_tool.options.disable_debug,
        disable_dry_run=registered_tool.options.disable_dry_run,
        disable_verbose=registered_tool.options.disable_verbose,
    )

    # Drop any '--' needed for restarting in the virtual environment.
    results = parser_driver.pre_parse(raw_arguments, raise_exceptions=True)
    return CLIPreResults(results.trailing_arguments,
                         debug=results.data.DEBUG,
                         dry_run=results.data.DRY_RUN,
                         verbose=results.data.VERBOSE,
                         )
