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
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Self

from .util.filesystem import search_folder_stack_for_file
from .util.log import abort, log_warning
from .util.python import load_configuration_script, symbols_to_dataclass


@dataclass
class Tool:
    """
    Tool specification.

    These members can also be initialized from jiig tool scripts with the
    variables represented by uppercase globals.
    """

    @dataclass
    class Options:
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

    # === Required members.

    tool_name: str
    """Tool name."""

    tool_root_folder: str
    """Tool base (root) folder."""

    root_task: str | ModuleType | Callable
    """Task reference to root of hierarchy."""

    # === Optional members. These either have default values or can be derived.

    driver: type | str | ModuleType = None
    """Driver class reference."""

    driver_variant: str = None
    """Driver variant name."""

    jiig_root_folder: str | Path = None
    """Jiig base (root) folder."""

    jiig_library_folder: str | Path = None
    """Jiig library base folder."""

    aliases_path: str | Path = None
    """Path to aliases file."""

    author: str = None
    """Tool author name."""

    build_folder: str | Path = None
    """Build output folder, if applicable."""

    copyright: str = None
    """Tool copyright."""

    description: str = None
    """Tool description."""

    doc_api_packages: list[str] = None
    """Package names for producing API documentation."""

    doc_api_packages_excluded: list[str] = None
    """Package names to exclude from API documentation."""

    doc_folder: str | Path = None
    """Documentation output folder, e.g. for Pdoc3 documentation."""

    library_folders: list[str] = None
    """Library folders to add to Python import path."""

    tool_options: Options = None
    """Various boolean behavior options."""

    parser_implementation: str = None
    """Parser implementation."""

    pip_packages: list[str] = None
    """Packages needed by virtual environment, if enabled."""

    project_name: str = None
    """Project name for documentation, defaults to capitalized tool name."""

    sub_task_label: str = None
    """Name used to label sub-task types."""

    test_folder: str | Path = None
    """Test folder path for loading unit tests."""

    top_task_label: str = None
    """Name used to label the top level task type."""

    venv_folder: str = None
    """Virtual environment root folder - JIIG_VENV_ROOT/<tool> is used if None."""

    version: str = None
    """Tool version identifier."""

    extra_symbols: dict[str, Any] = None
    """Imported symbols that from_symbols() could not assign."""

    runtime: type | str | ModuleType = None
    """Custom runtime context module or class reference (Runtime subclass)."""

    @classmethod
    def from_symbols(cls,
                     symbols: dict,
                     **defaults,
                     ) -> Self:
        """
        Convert symbols to tool object.

        Abort if conversion fails.

        :param symbols: tool symbols
        :return: Tool object based on tool module data
        :param defaults: optional defaults that may be used for missing attributes
        """
        # Hide this internal dependency locally.
        from jiig.internal.registration.tasks import TASK_REGISTRY
        try:
            # Convert tool options from a dictionary to a ToolOptions dataclass object.
            if 'TOOL_OPTIONS' in symbols:
                if isinstance(symbols['TOOL_OPTIONS'], dict):
                    symbols['TOOL_OPTIONS'] = symbols_to_dataclass(symbols['TOOL_OPTIONS'],
                                                                   Tool.Options)
                else:
                    log_warning('Ignoring TOOL_OPTIONS, because it is not a dictionary.')
                    del symbols['TOOL_OPTIONS']
            # Now convert all the relevant symbols to a Tool dataclass object.
            tool: Tool = symbols_to_dataclass(
                symbols,
                Tool,
                required=['tool_name', 'tool_root_folder'],
                optional=['root_task'],
                protected=['init_hook_functions', 'exit_hook_functions'],
                overflow='extra_symbols',
                from_uppercase=True,
                defaults=defaults,
            )
            if tool.root_task is None:
                tool.root_task = TASK_REGISTRY.guess_root_task(tool.tool_name)
                if tool.root_task is None:
                    abort('Root task could not be guessed.')
            return tool
        except (TypeError, ValueError) as symbol_exc:
            abort(str(symbol_exc))

    @classmethod
    def from_script(cls,
                    script_path: str | Path,
                    ) -> Self:
        """
        Convert tool script to object.

        Injects `jiig` import into execution symbols, so that a script can
        function without an explicit `import jiig` statement.

        :param script_path: script path
        :return: Tool object based on tool script data
        """
        import jiig
        if not isinstance(script_path, Path):
            script_path = Path(script_path)
        configuration = load_configuration_script(script_path, jiig=jiig)
        tool_name = script_path.name.replace('-', '_')
        # The script may be in a sub-folder, e.g. 'bin'. Look up the folder
        # stack for a folder that contains a library folder using the tool name.
        # If that isn't found fall back to the folder containing the script.
        tool_folder = os.path.dirname(os.path.realpath(script_path))
        library_file_name = os.path.join(tool_name, '__init__.py')
        library_root_folder = search_folder_stack_for_file(tool_folder, library_file_name)
        if library_root_folder:
            tool_folder = str(library_root_folder)
        return cls.from_symbols(configuration,
                                tool_name=tool_name,
                                tool_root_folder=tool_folder,
                                description=configuration.get('__doc__'))

    @classmethod
    def from_module(cls,
                    tool_module: object,
                    defaults: dict = None,
                    ) -> Self:
        """
        Convert tool module to object.

        :param tool_module: tool module
        :param defaults: optional defaults that may be used for missing attributes
        :return: Tool object based on tool module data
        :raise ValueError: if conversion fails due to bad input data
        :raise TypeError: if conversion fails due to bad output type
        """
        return cls.from_symbols(tool_module.__dict__, defaults=defaults)
