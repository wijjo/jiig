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

HOME_FOLDER_PATH = Path(os.environ['HOME'])
JIIG_ROOT = Path(__file__).parent.parent
JIIG_CONFIGURATION_NAME = 'jiig.yaml'
JIIG_VENV_ROOT = HOME_FOLDER_PATH / '.jiig-venv'
DEFAULT_AUTHOR = '(unknown author)'
DEFAULT_COPYRIGHT = '(unknown copyright)'
DEFAULT_TOOL_DESCRIPTION = '(no tool description)'
DEFAULT_VERSION = '(unknown version)'
DEFAULT_DOC_FOLDER = Path('doc')
DEFAULT_TEST_FOLDER = Path('tests')
DEFAULT_ALIASES_PATH = HOME_FOLDER_PATH / '.jiig-aliases'
DEFAULT_BUILD_FOLDER = Path('build')
SUB_TASK_LABEL = 'SUB_TASK'
TOP_TASK_LABEL = 'TASK'
TOP_TASK_DEST_NAME = 'TASK'
CORE_PIP_PACKAGES = ['PyYAML']
