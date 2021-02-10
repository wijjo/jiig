"""
Global option initialization using command line pre-processing.
"""

import sys
from dataclasses import dataclass
from typing import Text, List, Optional

from jiig import cli, model, const, util


@dataclass
class AppPreLoadData:
    """Preliminary results from pre-parsed command line."""

    runner_args: Optional[List[Text]]
    """Optional runner, e.g. jiig-run, preamble."""

    cli_args: List[Text]
    """Full command line arguments."""

    trailing_arguments: List[Text]
    """Unparsed trailing command line arguments."""

    parser_implementation: Text
    """Parser implementation name."""

    debug: bool
    """Enable debug processing if True."""

    dry_run: bool
    """Enable non-destructive run if True."""

    verbose: bool
    """Enable verbose messages if True."""


def go(tool_config: model.Tool,
       runner_args: Optional[List[Text]],
       cli_args: Optional[List[Text]],
       ) -> AppPreLoadData:
    """
    Initialize global options based on pre-parsed command line.

    :param tool_config: tool configuration
    :param runner_args: optional runner, e.g. jiig-run, preamble
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
        tool_config.tool_name,
        'pre-processing',
        implementation=tool_config.parser_implementation,
        disable_debug=tool_config.options.disable_debug,
        disable_dry_run=tool_config.options.disable_dry_run,
        disable_verbose=tool_config.options.disable_verbose,
    )

    # Drop any '--' needed for restarting in the virtual environment.
    results = parser_driver.pre_parse(raw_arguments, raise_exceptions=True)

    # Push options into libraries to keep a one-way dependency from Jiig to
    # independent libraries, without needing a back-channel for options.
    util.set_options(debug=results.data.DEBUG,
                     dry_run=results.data.DRY_RUN,
                     verbose=results.data.VERBOSE)
    cli.set_options(debug=results.data.DEBUG,
                    dry_run=results.data.DRY_RUN,
                    verbose=results.data.VERBOSE,
                    top_command_label=const.TOP_TASK_LABEL,
                    sub_command_label=const.SUB_TASK_LABEL)

    interp_data = AppPreLoadData(runner_args,
                                 cli_args,
                                 results.trailing_arguments,
                                 tool_config.parser_implementation,
                                 debug=results.data.DEBUG,
                                 dry_run=results.data.DRY_RUN,
                                 verbose=results.data.VERBOSE)

    return interp_data
