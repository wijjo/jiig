# Copyright (C) 2021-2022, Steven Cooper
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

"""Registry package symbols."""

from .context_registry import CONTEXT_REGISTRY, SelfRegisteringContextBase, ContextReference,\
    ContextImplementation, ContextRegistrationRecord, ContextRegistry
from .driver_registry import DRIVER_REGISTRY, SelfRegisteringDriverBase, DriverReference, \
    DriverImplementation, DriverRegistrationRecord, DriverRegistry
from .field import ArgumentAdapter, Field
from .hint_registry import HINT_REGISTRY
from .runtime import Runtime, RuntimeHelpGenerator
from .task_registry import TASK_REGISTRY, TaskRegistry, TaskReference, TaskImplementation, TaskFunction, \
    TaskRegistrationRecord, TaskField, AssignedTask, SubTaskList, SubTaskDict, SubTaskCollection
from .tool import Tool, ToolOptions, JIIG_VENV_ROOT, SUB_TASK_LABEL, TOP_TASK_LABEL, TOP_TASK_DEST_NAME
