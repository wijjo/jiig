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

"""Simple dataclasses, abstract classes, and type hinting types."""

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import (
    dataclass,
    field,
)
from pathlib import Path
from types import ModuleType
from typing import (
    Callable,
    Any,
)

from .constants import (
    DEFAULT_ALIASES_PATH,
    DEFAULT_AUTHOR,
    DEFAULT_BUILD_FOLDER,
    DEFAULT_COPYRIGHT,
    DEFAULT_DOC_FOLDER,
    DEFAULT_EMAIL,
    DEFAULT_TEST_FOLDER,
    DEFAULT_TOOL_DESCRIPTION,
    DEFAULT_URL,
    DEFAULT_VERSION,
    SUB_TASK_LABEL,
    TOP_TASK_LABEL,
)


# The best we can do for now for a task function type hint, because Callable has
# no syntax for variable keyword arguments.
#: Task function callable type.
TaskFunction = Callable
#: Task reference type, name, module, or function reference.
TaskReference = str | ModuleType | TaskFunction
#: Module reference type, name or explicit module.
ModuleReference = str | ModuleType
#: Argument adapter function callable type.
ArgumentAdapter = Callable[..., Any]


@dataclass
class ToolMetadata:
    """Runtime metadata.

    tool_name is the only required parameter.
    """
    #: Tool name, generally lowercase.
    tool_name: str
    #: Tool project name, generally capitalized.
    project_name: str = None
    #: Tool author.
    author: str = DEFAULT_AUTHOR
    #: Tool contact email.
    email: str = DEFAULT_EMAIL
    #: Tool copyright.
    copyright: str = DEFAULT_COPYRIGHT
    #: Tool description.
    description: str = DEFAULT_TOOL_DESCRIPTION
    #: Tool URL.
    url: str = DEFAULT_URL
    #: Tool version number.
    version: str = DEFAULT_VERSION
    #: Label for top task, used for help text.
    top_task_label: str = TOP_TASK_LABEL
    #: Label for sub-task, used for help text.
    sub_task_label: str = SUB_TASK_LABEL
    #: Pip packages required for virtual environment.
    pip_packages: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.project_name is None:
            self.project_name = self.tool_name.capitalize()


@dataclass
class ToolPaths:
    """Runtime folder paths."""
    #: Virtual environment path.
    venv: Path
    #: Tool base folder, with package containing task modules.
    base_folder: Path
    #: Aliases file path.
    aliases: Path = DEFAULT_ALIASES_PATH
    #: Build folder path.
    build: Path = DEFAULT_BUILD_FOLDER
    #: Documentation folder path.
    doc: Path = DEFAULT_DOC_FOLDER
    #: Test folder path.
    test: Path = DEFAULT_TEST_FOLDER


@dataclass
class ToolOptions:
    """Boolean options governing tool behavior."""
    #: Disable debug option if True.
    disable_debug: bool = False
    #: Disable dry run option if True.
    disable_dry_run: bool = False
    #: Disable verbose option if True.
    disable_verbose: bool = False
    #: Enable pause option if True.
    enable_pause: bool = False
    #: Enable keep files option if True.
    enable_keep_files: bool = False


@dataclass
class ToolCustomizations:
    """Tool customization data."""

    runtime: type | str | ModuleType | None
    """Custom runtime context module or class reference (Runtime subclass)."""

    driver: type | str | ModuleType | None
    """Driver class reference."""


class RuntimeHelpGenerator(ABC):
    """Abstract base class implemented by a driver to generate on-demand help output."""

    @abstractmethod
    def generate_help(self, *names: str, show_hidden: bool = False):
        """Provide help output.

        Args:
            *names: name parts (task name stack)
            show_hidden: show hidden task help if True
        """
        ...
