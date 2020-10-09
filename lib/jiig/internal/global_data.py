"""
Jiig global constants and data.
"""
import os
from typing import List, Text

from jiig.internal.types import ArgumentList, OptionDict, OptionDestFlagsDict

INIT_FILE = 'init.jiig'
ALIASES_PATH = os.path.expanduser('~/.jiig-aliases')
TEMPLATE_EXTENSION = '.template'
TEMPLATE_EXTENSION_EXE = '.template_exe'
TEMPLATE_EXTENSION_DOT = '.template_dot'
ALL_TEMPLATE_EXTENSIONS = [
    TEMPLATE_EXTENSION,
    TEMPLATE_EXTENSION_EXE,
    TEMPLATE_EXTENSION_DOT,
]
TOOL_TEMPLATES_FOLDER = 'tool-templates'
TEMPLATES_FOLDER = 'templates'
TASK_TEMPLATE = 'task.py.template'
TEMPLATE_FOLDER_SYMBOL_PATTERN = r'\(=(\w+)=\)'

# Folders prepended to sys.path.
LIBRARY_FOLDERS: List[Text] = []

# Default folders if not configured.
DEFAULT_TEST_FOLDER = 'test'

# Command line parsing constants.
CLI_DEST_NAME_PREFIX = 'TASK'
CLI_DEST_NAME_SEPARATOR = '.'
CLI_DEST_NAME_PREAMBLE = CLI_DEST_NAME_PREFIX + CLI_DEST_NAME_SEPARATOR
CLI_METAVAR_SUFFIX = 'SUB_TASK'
CLI_METAVAR_SEPARATOR = '_'

DEBUG = False
VERBOSE = False
DRY_RUN = False


def set_debug(value: bool):
    global DEBUG
    DEBUG = value


def set_verbose(value: bool):
    global VERBOSE
    VERBOSE = value


def set_dry_run(value: bool):
    global DRY_RUN
    DRY_RUN = value


def set_library_folders(folders: List[Text]):
    global LIBRARY_FOLDERS
    LIBRARY_FOLDERS = folders


class ToolOptions:
    name = None
    description = None
    epilog = None
    disable_alias = False
    disable_help = False
    disable_debug = False
    disable_dry_run = False
    disable_verbose = False
    common_arguments: ArgumentList = None
    common_options: OptionDict = {}
    common_flags_by_dest: OptionDestFlagsDict = {}
