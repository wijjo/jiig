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

"""Tool specification."""

import os
import sys
from dataclasses import dataclass, field
from typing import Any, cast

from ..driver import CLIDriver
from ..util.alias_catalog import DEFAULT_ALIASES_PATH
from ..util.log import abort, log_warning
from ..util.filesystem import search_folder_stack_for_file
from ..util.python import symbols_to_dataclass, load_configuration_script

from .context_registry import ContextReference
from .driver_registry import DriverReference
from .task_registry import TaskReference, AssignedTask, TASK_REGISTRY

# Constants.
DEFAULT_AUTHOR = '(unknown author)'
DEFAULT_BUILD_FOLDER = 'build'
DEFAULT_COPYRIGHT = '(unknown copyright)'
DEFAULT_TOOL_DESCRIPTION = '(no description, e.g. in tool script or class doc string)'
DEFAULT_DRIVER = CLIDriver
DEFAULT_DRIVER_VARIANT = 'argparse'
DEFAULT_DOC_FOLDER = 'doc'
DEFAULT_TEST_FOLDER = 'tests'
JIIG_VENV_ROOT = os.path.expanduser('~/.jiig-venv')
SUB_TASK_LABEL = 'SUB_TASK'
TOP_TASK_LABEL = 'TASK'
TOP_TASK_DEST_NAME = 'TASK'


@dataclass
class ToolOptions:
    """Boolean options governing tool behavior."""

    disable_alias: bool = False
    """Disable alias feature if True."""

    disable_help: bool = False
    """Disable help feature if True."""

    disable_debug: bool = False
    """Disable debug option if True."""

    disable_dry_run: bool = False
    """Disable dry run option if True."""

    disable_verbose: bool = False
    """Disable verbose option if True."""

    enable_pause: bool = False
    """Enable pause option if True."""

    enable_keep_files: bool = False
    """Enable keep files option if True."""

    hide_builtin_tasks: bool = False
    """Hide tasks like help, alias, venv, etc. from help."""

    venv_required: bool = False
    """Create a virtual environment even if no extra Pip packages are required."""


@dataclass
class Tool:
    """
    Tool specification.

    These members can also be initialized from jiig tool scripts with the
    variables represented by uppercase globals.
    """

    # === Required members.

    tool_name: str
    """Tool name."""

    tool_root_folder: str
    """Tool base (root) folder."""

    root_task: TaskReference
    """Task reference to root of hierarchy."""

    # === Optional members. These either have default values or can be derived.

    driver: DriverReference = DEFAULT_DRIVER
    """Driver class reference."""

    driver_variant: str = DEFAULT_DRIVER_VARIANT
    """Driver variant name."""

    jiig_root_folder: str = None
    """Jiig base (root) folder."""

    jiig_library_folder: str = None
    """Jiig library base folder."""

    aliases_path: str = DEFAULT_ALIASES_PATH
    """Path to aliases file."""

    author: str = DEFAULT_AUTHOR
    """Tool author name."""

    build_folder: str = DEFAULT_BUILD_FOLDER
    """Build output folder, if applicable."""

    copyright: str = DEFAULT_COPYRIGHT
    """Tool copyright."""

    description: str = DEFAULT_TOOL_DESCRIPTION
    """Tool description."""

    doc_api_packages: list[str] = field(default_factory=list)
    """Package names for producing API documentation."""

    doc_api_packages_excluded: list[str] = field(default_factory=list)
    """Package names to exclude from API documentation."""

    doc_folder: str = DEFAULT_DOC_FOLDER
    """Documentation output folder, e.g. for Pdoc3 documentation."""

    library_folders: list[str] = field(default_factory=list)
    """Library folders to add to Python import path."""

    tool_options: ToolOptions = field(default_factory=ToolOptions)
    """Various boolean behavior options."""

    parser_implementation: str = None
    """Parser implementation."""

    pip_packages: list[str] = field(default_factory=list)
    """Packages needed by virtual environment, if enabled."""

    project_name: str = None
    """Project name for documentation, defaults to capitalized tool name."""

    sub_task_label: str = SUB_TASK_LABEL
    """Name used to label sub-task types."""

    test_folder: str = DEFAULT_TEST_FOLDER
    """Test folder path for loading unit tests."""

    top_task_label: str = TOP_TASK_LABEL
    """Name used to label the top level task type."""

    venv_folder: str = None
    """Virtual environment root folder - JIIG_VENV_ROOT/<tool> is used if None."""

    version: str = '(unknown version)'
    """Tool version identifier."""

    extra_symbols: dict[str, Any] = field(default_factory=dict)
    """Imported symbols that from_symbols() could not assign."""

    runtime: ContextReference = None
    """Custom runtime context module or class reference (Runtime subclass)."""

    _assigned_root_task: AssignedTask | None = None
    """Populated on demand by resolving the root task reference."""

    def __post_init__(self):
        if self.jiig_library_folder is None:
            self.jiig_library_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if self.jiig_root_folder is None:
            self.jiig_root_folder = self.jiig_library_folder
        # Make `library_folders` a complete list of all needed paths.
        # Include tool and jiig library paths.
        if not self.library_folders:
            self.library_folders.append(self.tool_root_folder)
        if self.jiig_library_folder not in self.library_folders:
            self.library_folders.append(self.jiig_library_folder)
        if self.project_name is None:
            self.project_name = self.tool_name.capitalize()
        if self.venv_folder is None:
            self.venv_folder = os.path.join(os.path.expanduser(JIIG_VENV_ROOT), self.tool_name)

    @classmethod
    def from_symbols(cls, symbols: dict, **defaults) -> 'Tool':
        """
        Convert symbols to tool object.

        Abort if conversion fails.

        :param symbols: tool symbols
        :return: Tool object based on tool module data
        :param defaults: optional defaults that may be used for missing attributes
        """
        try:
            # Convert tool options from a dictionary to a ToolOptions dataclass object.
            if 'TOOL_OPTIONS' in symbols:
                if isinstance(symbols['TOOL_OPTIONS'], dict):
                    symbols['TOOL_OPTIONS'] = symbols_to_dataclass(symbols['TOOL_OPTIONS'],
                                                                   ToolOptions)
                else:
                    log_warning('Ignoring TOOL_OPTIONS, because it is not a dictionary.')
                    del symbols['TOOL_OPTIONS']
            # Now convert all the relevant symbols to a Tool dataclass object.
            dataclass_obj = symbols_to_dataclass(
                symbols,
                cls,
                required=['tool_name', 'tool_root_folder'],
                optional=['root_task'],
                protected=['init_hook_functions', 'exit_hook_functions'],
                overflow='extra_symbols',
                from_uppercase=True,
                defaults=defaults,
            )
            if dataclass_obj.root_task is None:
                dataclass_obj.root_task = \
                    TASK_REGISTRY.guess_root_task_implementation(dataclass_obj.tool_name)
                if dataclass_obj.root_task is None:
                    abort('Root task could not be guessed.')
            return cast(cls, dataclass_obj)
        except (TypeError, ValueError) as symbol_exc:
            abort(str(symbol_exc))

    @classmethod
    def from_script(cls, script_path: str) -> 'Tool':
        """
        Convert tool script to object.

        Injects `jiig` import into execution symbols, so that a script can
        function without an explicit `import jiig` statement.

        :param script_path: script path
        :return: Tool object based on tool script data
        """
        import jiig
        configuration = load_configuration_script(script_path, jiig=jiig)
        tool_name = os.path.basename(script_path).replace('-', '_')
        # The script may be in a sub-folder, e.g. 'bin'. Look up the folder
        # stack for a folder that contains a library folder using the tool name.
        # If that isn't found fall back to the folder containing the script.
        tool_folder = os.path.dirname(os.path.realpath(script_path))
        library_file_name = os.path.join(tool_name, '__init__.py')
        library_root_folder = search_folder_stack_for_file(tool_folder, library_file_name)
        if library_root_folder:
            tool_folder = library_root_folder
        description = configuration.get('__doc__', DEFAULT_TOOL_DESCRIPTION)
        return cls.from_symbols(configuration,
                                tool_name=tool_name,
                                tool_root_folder=tool_folder,
                                description=description)

    @classmethod
    def from_module(cls,
                    tool_module: object,
                    defaults: dict = None,
                    ) -> 'Tool':
        """
        Convert tool module to object.

        :param tool_module: tool module
        :param defaults: optional defaults that may be used for missing attributes
        :return: Tool object based on tool module data
        :raise ValueError: if conversion fails due to bad input data
        :raise TypeError: if conversion fails due to bad output type
        """
        return cls.from_symbols(tool_module.__dict__, defaults=defaults)

    @property
    def assigned_root_task(self) -> AssignedTask:
        """
        Assigned registered root task (populated on demand).

        :return: root task assigned to tool
        """
        if self._assigned_root_task is None:
            self._assigned_root_task = TASK_REGISTRY.resolve_assigned_task(
                self.root_task, '(root)', 2, required=True)
        return self._assigned_root_task

    @property
    def venv_interpreter(self) -> str:
        """
        Virtual environment Python interpreter path.

        :return: python path
        """
        return os.path.join(self.venv_folder, 'bin', 'python')

    @property
    def venv_active(self) -> True:
        """
        Check if virtual environment is active.

        :return: True if virtual environment is active
        """
        return sys.executable == self.venv_interpreter

    @property
    def venv_needed(self) -> True:
        """
        Check if virtual environment is needed.

        :return: True if virtual environment is needed
        """
        return self.pip_packages or self.tool_options.venv_required
