"""
Main Jiig initialization, including reading global parameters and command line preprocessing.
"""

import os
import sys
from dataclasses import dataclass
from typing import Text, List

from jiig.cli_parsing import get_parser_driver, ParserImplementations
from jiig.utility.console import log_message
from jiig.utility.init_file import ParamLoader, ParamList, ParamFolder, ParamFolderList, ParamBoolean

# Constants
FULL_NAME_SEPARATOR = '.'
DEST_NAME_SEPARATOR = '.'
DEFAULT_PARSER_IMPLEMENTATION = ParserImplementations.argparse
JIIG_TEMPLATES_FOLDER = 'templates'
JIIG_TASK_TEMPLATE = 'task.py.template'
TOOL_TEMPLATES_FOLDER = 'tool-templates'
INIT_FILE_NAME = 'init.jiig'
ALIASES_PATH = os.path.expanduser('~/.jiig-aliases')
DEFAULT_TEST_FOLDER = 'test'
TOP_TASK_LABEL = 'TASK'
SUB_TASK_LABEL = 'SUB_TASK'

# Init file parameter field definitions.
INIT_PARAM_TYPES = [
    ParamFolderList('LIB_FOLDERS', default_value=['lib']),
    ParamFolder('TEST_ROOT', default_value='test'),
    ParamFolder('VENV_ROOT', default_value='venv'),
    ParamBoolean('VENV_ENABLED', default_value=False),
    ParamList('PIP_PACKAGES', unique=True, default_value=[]),
]


# Returned data structure.
@dataclass
class ParameterData:
    jiig_run_script_path: Text
    jiig_root: Text
    jiig_lib: Text
    tool_script_path: Text
    tool_name: Text
    raw_arguments: List[Text]
    debug: bool
    dry_run: bool
    verbose: bool
    trailing_arguments: List[Text]
    library_folders: List[Text]
    venv_root: Text
    venv_enabled: bool
    pip_packages: List[Text]
    test_root: Text
    parser_implementation: Text
    aliases_path: Text
    init_file_name: Text
    top_task_label: Text
    sub_task_label: Text
    jiig_templates_folder: Text
    jiig_task_template: Text
    tool_templates_folder: Text
    full_name_separator: Text
    default_test_folder: Text


def initialize(command_line_arguments: List[Text]) -> ParameterData:
    """
    Initialize and pre-process command line arguments.

    :param command_line_arguments: raw command line arguments
    :return: initialized parameter data
    """
    jiig_run_script_path = command_line_arguments[0]
    jiig_root = os.path.dirname(os.path.realpath(jiig_run_script_path))
    jiig_lib = os.path.join(jiig_root, 'lib')
    tool_script_path = os.path.realpath(command_line_arguments[1])
    tool_name = os.path.splitext(os.path.basename(tool_script_path))[0]
    tool_root = os.path.dirname(tool_script_path)
    init_path = os.path.join(tool_root, INIT_FILE_NAME)

    # Get the raw arguments, filtering out '--', if inserted before trailing arguments.
    raw_arguments = command_line_arguments[2:]
    if raw_arguments and raw_arguments[0] == '--':
        raw_arguments = raw_arguments[1:]
    if raw_arguments is None:
        raw_arguments = command_line_arguments

    # Pre-parse raw arguments to get top level options and trailing arguments.
    parser_driver = get_parser_driver(
        tool_name,
        'pre-processing',
        implementation=DEFAULT_PARSER_IMPLEMENTATION)

    results = parser_driver.pre_parse(raw_arguments, raise_exceptions=True)
    # Drop the '--' that was needed for restarting in the virtual environment.
    if results.trailing_arguments and results.trailing_arguments[0] == '--':
        trailing_arguments = results.trailing_arguments[1:]
    else:
        trailing_arguments = results.trailing_arguments

    param_loader = ParamLoader(INIT_PARAM_TYPES)
    log_message(f'Load tool configuration file "{init_path}".', verbose=True)
    param_loader.load_file(init_path)
    init_params = param_loader.get_data()
    library_folders = []
    if init_params.LIB_FOLDERS:
        for tool_lib_folder in reversed(init_params.LIB_FOLDERS):
            if tool_lib_folder not in sys.path:
                library_folders.insert(0, tool_lib_folder)

    # Package and return initialized data.
    return ParameterData(jiig_run_script_path=jiig_run_script_path,
                         jiig_root=jiig_root,
                         jiig_lib=jiig_lib,
                         tool_script_path=tool_script_path,
                         tool_name=tool_name,
                         raw_arguments=raw_arguments,
                         debug=results.data.DEBUG,
                         dry_run=results.data.DRY_RUN,
                         verbose=results.data.VERBOSE,
                         trailing_arguments=trailing_arguments,
                         library_folders=library_folders,
                         venv_root=init_params.VENV_ROOT,
                         venv_enabled=init_params.VENV_ENABLED,
                         pip_packages=init_params.PIP_PACKAGES,
                         test_root=init_params.TEST_ROOT,
                         parser_implementation=DEFAULT_PARSER_IMPLEMENTATION,
                         aliases_path=ALIASES_PATH,
                         init_file_name=INIT_FILE_NAME,
                         top_task_label=TOP_TASK_LABEL,
                         sub_task_label=SUB_TASK_LABEL,
                         jiig_templates_folder=JIIG_TEMPLATES_FOLDER,
                         jiig_task_template=JIIG_TASK_TEMPLATE,
                         tool_templates_folder=TOOL_TEMPLATES_FOLDER,
                         full_name_separator=FULL_NAME_SEPARATOR,
                         default_test_folder=DEFAULT_TEST_FOLDER,
                         )
