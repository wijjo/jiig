import os
import re

from .cli_parsing import ParserImplementations

# TODO: Paths should become Windows-compatible eventually.
FULL_NAME_SEPARATOR = '.'
DEFAULT_PARSER_IMPLEMENTATION = ParserImplementations.argparse
JIIG_TEMPLATES_FOLDER = 'templates'
TOOL_TEMPLATES_FOLDER = f'{JIIG_TEMPLATES_FOLDER}/tool'
TASK_TEMPLATES_FOLDER = f'{JIIG_TEMPLATES_FOLDER}/task'
ALIASES_PATH = os.path.expanduser('~/.jiig-aliases')
JIIG_VENV_ROOT = os.path.expanduser('~/.jiig-venv')
TOP_TASK_LABEL = 'TASK'
SUB_TASK_LABEL = 'SUB_TASK'
VALID_NAME_REGEX = re.compile(r'^[a-z][a-z0-9\-_]*$')
DEFAULT_TEST_FOLDER = 'test'
DEFAULT_DOC_FOLDER = 'doc'
DEFAULT_BUILD_FOLDER = 'build'
TASK_MODULE_CLASS_NAME = 'TaskClass'
TOOL_MODULE_CLASS_NAME = 'ToolClass'
VENV_DISABLED = -1
VENV_OPTIONAL = 0
VENV_REQUIRED = 1
VENV_DEFAULT = VENV_OPTIONAL
