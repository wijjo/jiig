"""
Task execution initialization.
"""

import os

from jiig.registration.registered_tools import RegisteredTool

from .execution_data import ExecutionData
from .cli_processor import CLIResults


def initialize(exec_data: ExecutionData,
               registered_tool: RegisteredTool,
               cli_results: CLIResults):
    """
    Initialize tool execution.

    :param exec_data: script paths and command line arguments data
    :param registered_tool: registered tool, including tool class and venv_folder
    :param cli_results: results of command line parsing
    """
    registered_tool.run(cli_results.names,
                        cli_results.data,
                        cli_results.trailing_arguments,
                        exec_data.cli_args,
                        DEBUG=cli_results.data.DEBUG,
                        DRY_RUN=cli_results.data.DRY_RUN,
                        JIIG_LIB=exec_data.jiig_library_path,
                        JIIG_ROOT=exec_data.jiig_root,
                        JIIG_RUN_SCRIPT_PATH=exec_data.run_script_path,
                        PARSER_IMPLEMENTATION=exec_data.parser_implementation,
                        TOOL_ROOT=os.path.dirname(exec_data.tool_script_path),
                        TOOL_SCRIPT_PATH=exec_data.tool_script_path,
                        TRAILING_ARGUMENTS=cli_results.trailing_arguments,
                        VERBOSE=cli_results.data.VERBOSE,
                        )
