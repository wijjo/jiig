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

import os
from pathlib import Path

#: Jiig tool name.
JIIG_TOOL_NAME = 'jiig'
#: User home folder path.
HOME_FOLDER_PATH = Path(os.environ['HOME'])
#: Jiig root folder path.
JIIG_ROOT = Path(__file__).parent.parent
#: Default Jiig TOML format configuration file name.
JIIG_TOML_CONFIGURATION_NAME = 'jiig.toml'
#: Default Jiig JSON format configuration file name.
JIIG_JSON_CONFIGURATION_NAME = 'jiig.json'
#: Root folder path containing generated virtual environments.
JIIG_VENV_ROOT = HOME_FOLDER_PATH / '.jiig' / 'venvs'
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
#: Default folder path for generated documentation.
DEFAULT_DOC_FOLDER = Path('doc')
#: Default test folder path.
DEFAULT_TEST_FOLDER = Path('tests')
#: Default file path for Jiig aliases.
DEFAULT_ALIASES_PATH = HOME_FOLDER_PATH / '.jiig' / 'aliases'
#: Default build folder path.
DEFAULT_BUILD_FOLDER = Path('build')
#: Default name for root (top level) task.
DEFAULT_ROOT_TASK_NAME = '(root)'
#: Default help label for sub-tasks.
SUB_TASK_LABEL = 'SUB_TASK'
#: Default help label for top task.
TOP_TASK_LABEL = 'TASK'
#: Default argparse dest name for tasks.
TOP_TASK_DEST_NAME = 'TASK'
