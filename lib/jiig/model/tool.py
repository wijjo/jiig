"""
Tool registration class.
"""

import os
from dataclasses import dataclass, field
from typing import Text, List, Dict, Any, Type, Union, cast, Optional

from jiig import const
from jiig.util.python import symbols_to_dataclass


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

    venv_required: bool = False
    """Create a virtual environment even if no extra Pip packages are required."""


@dataclass
class Tool:
    """
    Tool specification.
    """
    # === Required members.

    tool_name: Text
    """Tool name."""

    tool_root_folder: Text
    """Tool base (root) folder."""

    root_task: Union[Type, Text, object]
    """Root of task config hierarchy."""

    # === Optional members. These either have default values or can be derived.

    jiig_root_folder: Text = None
    """Jiig base (root) folder."""

    jiig_library_folder: Text = None
    """Jiig library base folder."""

    aliases_path: Text = const.DEFAULT_ALIASES_PATH
    """Path to aliases file."""

    author: Text = const.DEFAULT_AUTHOR
    """Tool author name."""

    build_folder: Text = const.DEFAULT_BUILD_FOLDER
    """Build output folder, if applicable."""

    copyright: Text = const.DEFAULT_COPYRIGHT
    """Tool copyright."""

    description: Text = const.DEFAULT_DESCRIPTION
    """Tool description."""

    doc_api_packages: List[Text] = field(default_factory=list)
    """Package names for producing API documentation."""

    doc_api_packages_excluded: List[Text] = field(default_factory=list)
    """Package names to exclude from API documentation."""

    doc_folder: Text = const.DEFAULT_DOC_FOLDER
    """Documentation output folder, e.g. for Pdoc3 documentation."""

    library_folders: List[Text] = field(default_factory=list)
    """Library folders to add to Python import path."""

    options: ToolOptions = field(default_factory=ToolOptions)
    """Various boolean behavior options."""

    parser_implementation: Text = const.DEFAULT_PARSER_IMPLEMENTATION
    """Parser implementation, defaults to 'argparse'."""

    pip_packages: List[Text] = field(default_factory=list)
    """Packages needed by virtual environment, if enabled."""

    project_name: Text = None
    """Project name for documentation, defaults to capitalized tool name."""

    sub_task_label: Text = const.SUB_TASK_LABEL
    """Name used to label sub-task types."""

    test_folder: Text = const.DEFAULT_TEST_FOLDER
    """Test folder path for loading unit tests."""

    top_task_label: Text = const.TOP_TASK_LABEL
    """Name used to label the top level task type."""

    venv_folder: Text = None
    """Virtual environment root folder - JIIG_VENV_ROOT/<tool> is used if None."""

    version: Text = '(unknown version)'
    """Tool version identifier."""

    expansion_symbols: Dict[Text, Any] = field(default_factory=dict)
    """Symbols used for string and path template expansion."""

    @classmethod
    def from_symbols(cls,
                     symbols: Dict,
                     defaults: Dict = None,
                     ) -> 'Tool':
        """
        Convert symbols to tool object.

        :param symbols: tool symbols
        :return: JiigTool object based on tool module data
        :param defaults: optional defaults that may be used for missing attributes
        :raise ValueError: if conversion fails due to bad input data
        :raise TypeError: if conversion fails due to bad output type
        """
        dataclass_obj = symbols_to_dataclass(
            symbols,
            cls,
            required=['tool_name', 'tool_root_folder', 'root_task'],
            protected=['init_hook_functions', 'exit_hook_functions'],
            overflow='expansion_symbols',
            from_uppercase=True,
            defaults=defaults,
        )
        return cast(cls, dataclass_obj)

    @classmethod
    def from_module(cls,
                    tool_module: object,
                    defaults: Dict = None,
                    ) -> 'Tool':
        """
        Convert tool module to object.

        :param tool_module: tool module
        :param defaults: optional defaults that may be used for missing attributes
        :return: JiigTool object based on tool module data
        :raise ValueError: if conversion fails due to bad input data
        :raise TypeError: if conversion fails due to bad output type
        """
        return cls.from_symbols(tool_module.__dict__, defaults=defaults)


class ToolRuntime:
    """
    Wrapper for user Tool configuration that provides final Tool runtime data.

    @property's are used to enforce read-only access.
    """

    def __init__(self, tool: Tool):
        self._tool = tool
        if self._tool.jiig_library_folder is not None:
            self._jiig_library_folder = self._tool.jiig_library_folder
        else:
            self._jiig_library_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if self._tool.jiig_root_folder is not None:
            self._jiig_root_folder = self._tool.jiig_root_folder
        else:
            self._jiig_root_folder = os.path.dirname(self._jiig_library_folder)
        # Make `library_folders` a complete list of all needed paths.
        # Include tool and jiig library paths.
        self._library_folders: List[Text] = self._tool.library_folders or []
        if not self._library_folders:
            # Guess a default tool library folder.
            tool_library_folder = os.path.join(self.tool_root_folder,
                                               const.DEFAULT_LIBRARY_FOLDER)
            self._library_folders.append(tool_library_folder)
        if self.jiig_library_folder not in self._library_folders:
            self._library_folders.append(self.jiig_library_folder)
        if self._tool.project_name is not None:
            self._project_name = self._tool.project_name
        else:
            self._project_name = self._tool.tool_name.capitalize()
        if self._tool.venv_folder is not None:
            self._venv_folder = self._tool.venv_folder
        else:
            self._venv_folder = os.path.join(os.path.expanduser(const.JIIG_VENV_ROOT),
                                             self._tool.tool_name)
        # Expansion symbols are cached on demand.
        self._expansion_symbols: Optional[Dict[Text, Any]] = None

    @property
    def name(self) -> Text:
        """
        Tool name.

        :return: tool name
        """
        return self._tool.tool_name

    @property
    def tool_root_folder(self) -> Text:
        """
        Tool base (root) folder.

        :return: tool root folder
        """
        return self._tool.tool_root_folder

    @property
    def root_task_spec(self) -> Union[Type, Text, object]:
        """
        Root task runtime data.

        :return: root TaskRuntime
        """
        return self._tool.root_task

    @property
    def jiig_root_folder(self) -> Text:
        """
        Jiig root folder, with default based on library folder path.

        :return: Jiig root folder
        """
        return self._jiig_root_folder

    @property
    def jiig_library_folder(self) -> Text:
        """
        Jiig library folder, with default based on this module's path.

        :return: Jiig library folder
        """
        return self._jiig_library_folder

    @property
    def aliases_path(self) -> Text:
        """
        Path to aliases file.

        :return: aliases file path
        """
        return self._tool.aliases_path

    @property
    def author(self) -> Text:
        """
        Tool author name.

        :return: author name
        """
        return self._tool.author

    @property
    def build_folder(self) -> Text:
        """
        Build output folder, if applicable.

        :return: build folder
        """
        return self._tool.build_folder

    @property
    def copyright(self) -> Text:
        """
        Tool copyright.

        :return: copyright text
        """
        return self._tool.copyright

    @property
    def description(self) -> Text:
        """
        Tool description.

        :return: description text
        """
        return self._tool.description

    @property
    def doc_api_packages(self) -> List[Text]:
        """
        Package names for producing API documentation.

        :return: doc API package list
        """
        return self._tool.doc_api_packages

    @property
    def doc_api_packages_excluded(self) -> List[Text]:
        """
        Package names to exclude from API documentation.

        :return: excluded doc API package list
        """
        return self._tool.doc_api_packages_excluded

    @property
    def doc_folder(self) -> Text:
        """
        Documentation output folder, if applicable, e.g. for Pdoc3 documentation.

        :return: documentation output folder
        """
        return self._tool.doc_folder

    @property
    def library_folders(self) -> List[Text]:
        """
        Library folders to add to Python import path.

        :return: library folder list
        """
        return self._library_folders

    @property
    def options(self) -> ToolOptions:
        """
        Various boolean behavior options.

        :return: tool options
        """
        return self._tool.options

    @property
    def parser_implementation(self) -> Text:
        """
        Parser implementation, defaults to 'argparse'.

        :return: parser implementation name
        """
        return self._tool.parser_implementation

    @property
    def pip_packages(self) -> List[Text]:
        """
        Packages needed by virtual environment, if enabled.

        :return: pip package list
        """
        return self._tool.pip_packages

    @property
    def project_name(self) -> Text:
        """
        Project name for documentation, defaults to capitalized tool name.

        :return: project name
        """
        return self._project_name

    @property
    def sub_task_label(self) -> Text:
        """
        Name used to label sub-task types.

        :return: label text
        """
        return self._tool.sub_task_label

    @property
    def test_folder(self) -> Text:
        """
        Test folder path for loading unit tests.

        :return: test folder path
        """
        return self._tool.test_folder

    @property
    def top_task_label(self) -> Text:
        """
        Name used to label the top level task type.

        :return: label text
        """
        return self._tool.top_task_label

    @property
    def venv_folder(self) -> Text:
        """
        Virtual environment root folder, defaults to JIIG_VENV_ROOT/<tool>.

        :return: virtual environment root folder
        """
        return self._venv_folder

    @property
    def version(self) -> Text:
        """
        Tool version identifier.

        :return: version label
        """
        return self._tool.version

    @property
    def expansion_symbols(self) -> Dict:
        """
        Symbols used for string and path template expansion.

        :return: full expansion symbol dictionary
        """
        if self._expansion_symbols is None:
            self._expansion_symbols = {
                'aliases_path': self.aliases_path,
                'author': self.author,
                'build_folder': self.build_folder,
                'copyright': self.copyright,
                'description': self.description,
                'doc_folder': self.doc_folder,
                'jiig_library_folder': self.jiig_library_folder,
                'jiig_root_folder': self.jiig_root_folder,
                'project_name': self.project_name,
                'sub_task_label': self.sub_task_label,
                'tool_name': self.name,
                'tool_root_folder': self.tool_root_folder,
                'top_task_label': self.top_task_label,
                'venv_folder': self.venv_folder,
                'version': self.version,
            }
            self._expansion_symbols.update(self._tool.expansion_symbols)
        return self._expansion_symbols
