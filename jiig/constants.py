# Copyright (C) 2021-2023, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""Constants."""

from pathlib import Path

#: Jiig tool name.
JIIG_TOOL_NAME = 'jiig'
#: User home folder path.
HOME_FOLDER_PATH = Path.home()
#: Jiig root folder path.
JIIG_ROOT = Path(__file__).parent.parent
#: Default Jiig TOML format configuration file name.
JIIG_TOML_CONFIGURATION_NAME = 'jiig.toml'
#: Default Jiig JSON format configuration file name.
JIIG_JSON_CONFIGURATION_NAME = 'jiig.json'
#: Root folder path containing generated virtual environments.
JIIG_CONFIG_ROOT = HOME_FOLDER_PATH / '.jiig'
#: Environment variable that can override Jiig configuration root.
JIIG_CONFIG_ROOT_ENV_VAR = 'JIIG_CONFIG_ROOT'
#: Aliases catalog file name.
ALIASES_CATALOG_FILE_NAME = 'aliases.json'
#: Parameters catalog file name.
PARAMS_CATALOG_FILE_NAME = 'params.json'
#: Virtual environment folder name.
VENV_FOLDER_NAME = 'venv'
#: Default tool author string.
DEFAULT_AUTHOR = '(unknown author)'
#: Default tool copyright string.
DEFAULT_COPYRIGHT = '(unknown copyright)'
#: Default tool email string.
DEFAULT_EMAIL = ''
#: Default tool description string.
DEFAULT_TOOL_DESCRIPTION = '(no tool description)'
#: Default tool URL.
DEFAULT_URL = ''
#: Default tool version number.
DEFAULT_VERSION = '(unknown version)'
#: Default folder name containing generated documentation.
DEFAULT_DOC_FOLDER_NAME = 'doc'
#: Default test folder name.
DEFAULT_TESTS_FOLDER_NAME = 'tests'
#: Default build folder name.
DEFAULT_BUILD_FOLDER_NAME = 'build'
#: Default name for root (top level) task.
DEFAULT_ROOT_TASK_NAME = '(root)'
#: Default help label for sub-tasks.
SUB_TASK_LABEL = 'SUB_TASK'
#: Default help label for top task.
TOP_TASK_LABEL = 'TASK'
#: Default argparse dest name for tasks.
TOP_TASK_DEST_NAME = 'TASK'
#: Built-in task name format used by external tools.
BUILTIN_TASK_NAME_FORMAT = '__{}__'
#: Built-in task name regular expression pattern for parsing.
BUILTIN_TASK_NAME_PATTERN = r'__(\w+)__'
