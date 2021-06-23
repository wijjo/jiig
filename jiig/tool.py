"""Tool specification."""

import os
from dataclasses import dataclass, field
from typing import Text, List, Dict, Any, cast

from .driver import CLIDriver
from .registry import CONTEXT_REGISTRY, DRIVER_REGISTRY, TASK_REGISTRY
from .util.alias_catalog import DEFAULT_ALIASES_PATH
from .util.console import abort, log_warning
from .util.filesystem import search_folder_stack_for_file
from .util.python import symbols_to_dataclass, load_configuration_script

DEFAULT_AUTHOR = '(unknown author)'
DEFAULT_BUILD_FOLDER = 'build'
DEFAULT_COPYRIGHT = '(unknown copyright)'
DEFAULT_DESCRIPTION = '(no description)'
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

    These members can also be initialized from jiig-run scripts with the
    variables represented by uppercase globals.
    """

    # === Required members.

    tool_name: Text
    """Tool name."""

    tool_root_folder: Text
    """Tool base (root) folder."""

    root_task: TASK_REGISTRY.Reference
    """Root of task config hierarchy."""

    # === Optional members. These either have default values or can be derived.

    driver: DRIVER_REGISTRY.Reference = DEFAULT_DRIVER
    """Driver class reference."""

    driver_variant: Text = DEFAULT_DRIVER_VARIANT
    """Driver variant name."""

    jiig_root_folder: Text = None
    """Jiig base (root) folder."""

    jiig_library_folder: Text = None
    """Jiig library base folder."""

    aliases_path: Text = DEFAULT_ALIASES_PATH
    """Path to aliases file."""

    author: Text = DEFAULT_AUTHOR
    """Tool author name."""

    build_folder: Text = DEFAULT_BUILD_FOLDER
    """Build output folder, if applicable."""

    copyright: Text = DEFAULT_COPYRIGHT
    """Tool copyright."""

    description: Text = DEFAULT_DESCRIPTION
    """Tool description."""

    doc_api_packages: List[Text] = field(default_factory=list)
    """Package names for producing API documentation."""

    doc_api_packages_excluded: List[Text] = field(default_factory=list)
    """Package names to exclude from API documentation."""

    doc_folder: Text = DEFAULT_DOC_FOLDER
    """Documentation output folder, e.g. for Pdoc3 documentation."""

    library_folders: List[Text] = field(default_factory=list)
    """Library folders to add to Python import path."""

    tool_options: ToolOptions = field(default_factory=ToolOptions)
    """Various boolean behavior options."""

    parser_implementation: Text = None
    """Parser implementation."""

    pip_packages: List[Text] = field(default_factory=list)
    """Packages needed by virtual environment, if enabled."""

    project_name: Text = None
    """Project name for documentation, defaults to capitalized tool name."""

    sub_task_label: Text = SUB_TASK_LABEL
    """Name used to label sub-task types."""

    test_folder: Text = DEFAULT_TEST_FOLDER
    """Test folder path for loading unit tests."""

    top_task_label: Text = TOP_TASK_LABEL
    """Name used to label the top level task type."""

    venv_folder: Text = None
    """Virtual environment root folder - JIIG_VENV_ROOT/<tool> is used if None."""

    version: Text = '(unknown version)'
    """Tool version identifier."""

    extra_symbols: Dict[Text, Any] = field(default_factory=dict)
    """Imported symbols that from_symbols() could not assign."""

    runtime: CONTEXT_REGISTRY.Reference = None
    """Custom runtime context module or class reference (Runtime subclass)."""

    @classmethod
    def from_symbols(cls, symbols: Dict, **defaults) -> 'Tool':
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
                required=['tool_name', 'tool_root_folder', 'root_task'],
                protected=['init_hook_functions', 'exit_hook_functions'],
                overflow='extra_symbols',
                from_uppercase=True,
                defaults=defaults,
            )
            return cast(cls, dataclass_obj)
        except (TypeError, ValueError) as symbol_exc:
            abort(str(symbol_exc))

    @classmethod
    def from_script(cls, script_path: Text) -> 'Tool':
        """
        Convert tool script to object.

        :param script_path: script path
        :return: Tool object based on tool script data
        """
        configuration = load_configuration_script(script_path)
        tool_name = os.path.basename(script_path).replace('-', '_')
        # The script may be in a sub-folder, e.g. 'bin'. Look up the folder
        # stack for a folder that contains a library folder using the tool name.
        # If that isn't found fall back to the folder containing the script.
        tool_folder = os.path.dirname(os.path.realpath(script_path))
        library_file_name = os.path.join(tool_name, '__init__.py')
        library_root_folder = search_folder_stack_for_file(tool_folder, library_file_name)
        if library_root_folder:
            tool_folder = library_root_folder
        return cls.from_symbols(configuration,
                                tool_name=tool_name,
                                tool_root_folder=tool_folder)

    @classmethod
    def from_module(cls,
                    tool_module: object,
                    defaults: Dict = None,
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
