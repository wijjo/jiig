# Copyright (C) 2020-2022, Steven Cooper
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

TODO: <more library documentation goes here>
"""

# Key types and functions exposed at the top level.
from .decorators import task
from .driver import Driver, DriverTask
from .contexts import Context, ActionContext
from .registry import AssignedTask, Field, ArgumentAdapter, \
    Runtime, RuntimeHelpGenerator, Tool, ToolOptions, JIIG_VENV_ROOT
from .startup import main
from .util.options import OPTIONS
from .util.script import Script

# Top level public modules and their shortened aliases.
from . import adapters as a
from . import fields as f
from . import contexts as c
from . import adapters, fields, contexts, driver, util, tasks
