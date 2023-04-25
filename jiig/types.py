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

"""Type inspection data types."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Sequence, Any

from .constants import (
    DEFAULT_AUTHOR,
    DEFAULT_COPYRIGHT,
    DEFAULT_EMAIL,
    DEFAULT_TOOL_DESCRIPTION,
    DEFAULT_URL,
    DEFAULT_VERSION,
    SUB_TASK_LABEL,
    TOP_TASK_LABEL,
)


# The best we can do for now for a task function type hint, because Callable has
# no syntax for variable keyword arguments.
TaskFunction = Callable
TaskReference = str | ModuleType | TaskFunction
ModuleReference = str | ModuleType
SubTaskList = Sequence[TaskReference]
SubTaskDict = dict[str, TaskReference]
SubTaskCollection = SubTaskList | SubTaskDict
ArgumentAdapter = Callable[..., Any]


TOOL_METADATA_STRING_DEFAULT = '<placeholder>'


@dataclass
class ToolMetadata:
    """Runtime metadata.

    tool_name is the only required parameter.
    """
    tool_name: str
    project_name: str = TOOL_METADATA_STRING_DEFAULT
    author: str = DEFAULT_AUTHOR
    email: str = DEFAULT_EMAIL
    copyright: str = DEFAULT_COPYRIGHT
    description: str = DEFAULT_TOOL_DESCRIPTION
    url: str = DEFAULT_URL
    version: str = DEFAULT_VERSION
    top_task_label: str = TOP_TASK_LABEL
    sub_task_label: str = SUB_TASK_LABEL
    pip_packages: list[str] = field(default_factory=list)
    doc_api_packages: list[str] = field(default_factory=list)
    doc_api_packages_excluded: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.project_name == TOOL_METADATA_STRING_DEFAULT:
            self.project_name = self.tool_name.capitalize()


@dataclass
class ToolPaths:
    """Runtime folder paths."""
    libraries: list[Path]
    venv: Path
    aliases: Path
    build: Path
    doc: Path
    test: Path
    jiig_source_root: Path | None = None
    tool_source_root: Path | None = None
    library_path: str = field(init=False)

    def __post_init__(self):
        self.library_path = os.pathsep.join([str(p) for p in self.libraries])
