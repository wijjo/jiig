"""
Task execution initialization.
"""

from typing import List, Text

from jiig import model

from .cli_processor import CLIParseData


def initialize(cli_args: List[Text],
               registered_tool: model.RegisteredTool,
               cli_results: CLIParseData):
    """
    Initialize tool execution.

    :param cli_args: command line arguments
    :param registered_tool: registered tool, including tool class and venv_folder
    :param cli_results: results of command line parsing
    """
    runtime_options = model.RuntimeOptions(
        debug=cli_results.data.DEBUG,
        dry_run=cli_results.data.DRY_RUN,
        verbose=cli_results.data.VERBOSE,
    )

    registered_tool.run(cli_results.names,
                        runtime_options,
                        cli_results.data,
                        cli_results.trailing_arguments,
                        cli_args,
                        )
