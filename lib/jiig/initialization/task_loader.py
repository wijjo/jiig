"""
Task execution initialization.
"""

import os

from jiig import constants
from jiig.cli_parsing import ParseResults
from ..registration.registered_tools import RegisteredTool

from .execution_data import ExecutionData


def initialize(exec_data: ExecutionData,
               registered_tool: RegisteredTool,
               parse_results: ParseResults):
    """
    Initialize tool execution.

    :param exec_data: script paths and command line arguments data
    :param registered_tool: registered tool, including tool class and venv_folder
    :param parse_results: parsed raw argument data and trailing arguments, if any
    """
    registered_tool.run(parse_results.names,
                        parse_results.data,
                        parse_results.trailing_arguments,
                        exec_data.cli_args,
                        ALIASES_PATH=constants.ALIASES_PATH,
                        DEBUG=parse_results.data.DEBUG,
                        DEFAULT_TEST_FOLDER=constants.DEFAULT_TEST_FOLDER,
                        DRY_RUN=parse_results.data.DRY_RUN,
                        FULL_NAME_SEPARATOR=constants.FULL_NAME_SEPARATOR,
                        JIIG_LIB=exec_data.jiig_library_path,
                        JIIG_ROOT=exec_data.jiig_root,
                        JIIG_RUN_SCRIPT_PATH=exec_data.run_script_path,
                        JIIG_TEMPLATES_FOLDER=constants.JIIG_TEMPLATES_FOLDER,
                        PARSER_IMPLEMENTATION=exec_data.parser_implementation,
                        PIP_PACKAGES=registered_tool.options.pip_packages,
                        SUB_TASK_LABEL=constants.SUB_TASK_LABEL,
                        TASK_TEMPLATES_FOLDER=constants.TASK_TEMPLATES_FOLDER,
                        TEST_FOLDER=registered_tool.options.test_folder,
                        TOOL_NAME=registered_tool.tool_name,
                        TOOL_ROOT=os.path.dirname(exec_data.tool_script_path),
                        TOOL_SCRIPT_PATH=exec_data.tool_script_path,
                        TOOL_TEMPLATES_FOLDER=constants.TOOL_TEMPLATES_FOLDER,
                        TOP_TASK_LABEL=constants.TOP_TASK_LABEL,
                        TRAILING_ARGUMENTS=parse_results.trailing_arguments,
                        VENV_ENABLED=registered_tool.options.venv_enabled,
                        VENV_FOLDER=registered_tool.options.venv_folder,
                        VERBOSE=parse_results.data.VERBOSE,
                        )
