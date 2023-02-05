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

"""Type inspection types."""

from types import ModuleType
from typing import Callable, Sequence, Any

# The best we can do for now for a task function type hint, because Callable has
# no syntax for variable keyword arguments.
TaskFunction = Callable
TaskReference = str | ModuleType | TaskFunction
ModuleReference = str | ModuleType
SubTaskList = Sequence[TaskReference]
SubTaskDict = dict[str, TaskReference]
SubTaskCollection = SubTaskList | SubTaskDict
ArgumentAdapter = Callable[..., Any]
