# Copyright (C) 2020-2023, Steven Cooper
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

"""
Jiig library.
"""

# Top-level imports to allow task implementations to just import jiig. These
# must have minimal dependencies in order to avoid inadvertent circular imports.
from .context import Context
from .action_context import ActionContext
from .runtime import Runtime, RuntimeHelpGenerator
from .task import (
    Task,
    TaskGroup,
    TaskTree,
    task,
)
from .types import ToolMetadata, ToolPaths
from .util.options import OPTIONS
from .util.script import Script

# Top level public modules and their shortened aliases.
from . import adapters
from . import adapters as a
from . import fields
from . import fields as f
