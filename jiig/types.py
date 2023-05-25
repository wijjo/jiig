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
    ALIASES_CATALOG_FILE_NAME,
    DEFAULT_AUTHOR,
    DEFAULT_COPYRIGHT,
    DEFAULT_EMAIL,
    DEFAULT_TOOL_DESCRIPTION,
    DEFAULT_URL,
    DEFAULT_VERSION,
    JIIG_CONFIG_ROOT,
    PARAMS_CATALOG_FILE_NAME,
    SUB_TASK_LABEL,
    TOP_TASK_LABEL,
)
from .util.default import DefaultValue
from .util.repetition import Repetition


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
class TaskField:
    """Data extracted from task dataclass or task function signature."""
    #: Task name.
    name: str
    #: Task description.
    description: str
    #: Scalar element type.
    element_type: Any
    #: Field type.
    field_type: Any
    #: Optional field default value,
    default: DefaultValue | None
    #: Optional field repetition.
    repeat: Repetition | None
    #: Optional field choices list.
    choices: list | None
    #: Argument conversion/validation adapters.
    adapters: list[ArgumentAdapter]


@dataclass
class Field:
    """Field specification derived from type annotation.

    Use wrap_field(), instead of creating directly.
    """
    #: Scalar element type.
    element_type: Any
    #: Field description.
    description: str
    #: Field type (defaults to element_type if missing).
    field_type: Any
    #: optional field adapter function chain.
    adapters: list[ArgumentAdapter] | None
    #: Optional field repetition data.
    repeat: Repetition | None
    #: Optional value choices.
    choices: list | None


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
    #: Jiig configuration root folder (default: constants.JIIG_CONFIG_ROOT).
    jiig_config_root: Path = None

    def __post_init__(self):
        if self.project_name is None:
            self.project_name = self.tool_name.capitalize()
        if self.jiig_config_root is None:
            self.jiig_config_root = JIIG_CONFIG_ROOT

    @property
    def aliases_catalog_path(self) -> Path:
        """
        Provide path to aliases catalog file.

        Returns:
            path to aliases catalog file
        """
        return self.jiig_config_root / self.tool_name / ALIASES_CATALOG_FILE_NAME

    @property
    def params_catalog_path(self) -> Path:
        """
        Provide path to tool parameters catalog file.

        Returns:
            path to tool parameters catalog file
        """
        return self.jiig_config_root / self.tool_name / PARAMS_CATALOG_FILE_NAME


@dataclass
class ToolPaths:
    """Runtime folder paths."""
    #: Virtual environment path.
    venv: Path
    #: Tool base folder, with package containing task modules.
    base_folder: Path
    #: Aliases catalog file path.
    aliases_catalog_path: Path
    #: Values catalog file path.
    params_catalog_path: Path
    #: Build folder path.
    build: Path
    #: Documentation folder path.
    doc: Path
    #: Test folder path.
    test: Path


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

    #: Custom runtime context module or class reference (Runtime subclass).
    runtime: type | str | ModuleType | None

    #: Driver class reference.
    driver: type | str | ModuleType | None


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


@dataclass
class ToolParamValue:
    """"Value and location where value applies."""

    #: Value data.
    value: Any

    #: Description of value.
    description: str

    #: Folder hierarchy location where value applies. None is everywhere.
    location: Path | None


#: Dictionary mapping names to tool parameters/locations.
ToolParamsDictionary = dict[str, ToolParamValue]
