"""
Global option initialization using command line pre-processing.
"""

import sys
from dataclasses import dataclass
from typing import Text, List, Optional

from jiig import cli, model


@dataclass
class CLIPreParseData:
    """Preliminary results from pre-parsed command line."""
    trailing_arguments: List[Text]
    debug: bool = False
    dry_run: bool = False
    verbose: bool = False


def initialize(bootstrap: model.ToolBootstrap,
               cli_args: Optional[List[Text]],
               ) -> CLIPreParseData:
    """
    Initialize global options based on pre-parsed command line.

    :param bootstrap: tool bootstrap object
    :param cli_args: command line arguments to override the default, sys.argv[1:]
    :return: pre-processed command line data
    """
    if cli_args is None:
        cli_args = sys.argv[1:]

    # Get the raw arguments, filtering out '--', if inserted before trailing arguments
    # after restarting in the virtual environment.
    if cli_args and cli_args[0] == '--':
        raw_arguments = cli_args[1:]
    else:
        raw_arguments = cli_args

    # Pre-parse raw arguments to get top level options and trailing arguments.
    parser_driver = cli.get_parser_driver(
        bootstrap.tool_name,
        'pre-processing',
        implementation=bootstrap.parser_implementation,
        disable_debug=bootstrap.disable_debug,
        disable_dry_run=bootstrap.disable_dry_run,
        disable_verbose=bootstrap.disable_verbose,
    )

    # Drop any '--' needed for restarting in the virtual environment.
    results = parser_driver.pre_parse(raw_arguments, raise_exceptions=True)
    return CLIPreParseData(results.trailing_arguments,
                           debug=results.data.DEBUG,
                           dry_run=results.data.DRY_RUN,
                           verbose=results.data.VERBOSE,
                           )
