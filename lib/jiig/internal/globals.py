"""
Jiig global constants and data.
"""
import os

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

# Command line parsing constants.
CLI_DEST_NAME_PREFIX = 'TASK'
CLI_DEST_NAME_SEPARATOR = '.'
CLI_DEST_NAME_PREAMBLE = CLI_DEST_NAME_PREFIX + CLI_DEST_NAME_SEPARATOR
CLI_METAVAR_SUFFIX = 'SUB_TASK'
CLI_METAVAR_SEPARATOR = '_'

DEBUG = False
VERBOSE = False
DRY_RUN = False
