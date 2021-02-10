"""
Jiig global constants.
"""

import os
import re

from .cli import ParserImplementations

# TODO: Paths should become Windows-compatible eventually.
DEFAULT_ALIASES_PATH = os.path.expanduser('~/.jiig-aliases')
DEFAULT_AUTHOR = '(unknown author)'
DEFAULT_BUILD_FOLDER = 'build'
DEFAULT_COPYRIGHT = '(unknown copyright)'
DEFAULT_DESCRIPTION = '(no description)'
DEFAULT_DOC_FOLDER = 'doc'
DEFAULT_LIBRARY_FOLDER = 'lib'
DEFAULT_PARSER_IMPLEMENTATION = ParserImplementations.argparse
DEFAULT_TEST_FOLDER = 'test'
DEFAULT_VERSION = '0.1'
FULL_NAME_SEPARATOR = '.'
JIIG_VENV_ROOT = os.path.expanduser('~/.jiig-venv')
JIIG_TEMPLATES_FOLDER = 'templates'
SUB_TASK_LABEL = 'SUB_TASK'
TASK_MODULE_GLOBAL_NAME = 'TASK'
TASK_TEMPLATES_FOLDER = f'{JIIG_TEMPLATES_FOLDER}/task'
TOOL_CONFIGURATION_FILE_NAME = 'jiig.init'
TOOL_INIT_FUNCTION_NAME = 'tool_init'
TOOL_MODULE_GLOBAL_NAME = 'TOOL'
TOOL_TEMPLATES_FOLDER = f'{JIIG_TEMPLATES_FOLDER}/tool'
TOP_TASK_LABEL = 'TASK'
VALID_NAME_REGEX = re.compile(r'^[a-z][a-z0-9\-_]*$')
