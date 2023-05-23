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

"""Internal initialization package."""

from .aliases_catalog import create_aliases_catalog
from .arguments import prepare_arguments
from .driver import prepare_driver
from .params_catalog import create_params_catalog
from .runtime import prepare_runtime
from .tasks import prepare_tasks
from .tool_environment import prepare_tool_environment
from .virtual_environment import prepare_virtual_environment
