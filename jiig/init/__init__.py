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

"""Internal package."""

from .arguments import prepare_runtime_arguments, expand_arguments
from .venv import check_virtual_environment
from .tool import load_tool
from .driver import load_driver
from .builtin_tasks import inject_builtin_tasks
from .runtime_tasks import prepare_runtime_tasks
from .help import prepare_help_generator
from .runtime import prepare_runtime_object
from .execution import execute_application
