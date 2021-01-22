"""
Jiig tool bootstrap class.
"""

from dataclasses import dataclass, field
import os
from typing import Text, List, Dict, Any

from jiig import const


@dataclass
class ToolConfiguration:
    """Tool bootstrap configuration and start hook."""

    # === Required members.

    tool_name: Text
    """Tool name."""

    tool_root_folder: Text
    """Tool base (root) folder."""

    # === Optional members.

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

    doc_api_packages: List[Text] = field(default_factory=list)
    """Package names for producing API documentation."""

    doc_api_packages_excluded: List[Text] = field(default_factory=list)
    """Package names to exclude from API documentation."""

    doc_folder: Text = const.DEFAULT_DOC_FOLDER
    """Documentation output folder, e.g. for Pdoc3 documentation."""

    library_folders: List[Text] = field(default_factory=list)
    """Library folders to add to Python import path."""

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

    venv_required: bool = False
    """Create a virtual environment even if no extra Pip packages are required."""

    version: Text = '(unknown version)'
    """Tool version identifier."""

    expansion_symbols: Dict[Text, Any] = field(default_factory=dict)
    """Symbols used for string and path template expansion."""

    def __post_init__(self):
        # Seed expansion symbols with select attributes.
        if self.venv_folder is None:
            self.venv_folder = os.path.join(os.path.expanduser(const.JIIG_VENV_ROOT),
                                            self.tool_name)
        if self.project_name is None:
            self.project_name = self.tool_name.capitalize()
        # Replace missing Jiig library folder with path based on this module's path.
        if self.jiig_library_folder is None:
            this_module_folder = os.path.dirname(__file__)
            jiig_library_root_folder = os.path.dirname(this_module_folder)
            self.jiig_library_folder = os.path.dirname(jiig_library_root_folder)
        # Make `library_folders` a complete list of all needed paths.
        # Include tool and jiig library paths.
        if not self.library_folders:
            # Guess a default tool library folder.
            tool_library_folder = os.path.join(self.tool_root_folder,
                                               const.DEFAULT_LIBRARY_FOLDER)
            self.library_folders.append(tool_library_folder)
        if self.jiig_library_folder not in self.library_folders:
            self.library_folders.append(self.jiig_library_folder)
        # Merge string expansion symbols.
        self.expansion_symbols.update(
            aliases_path=self.aliases_path,
            author=self.author,
            build_folder=self.build_folder,
            copyright=self.copyright,
            description=self.description,
            doc_folder=self.doc_folder,
            jiig_library_folder=self.jiig_library_folder,
            jiig_root_folder=self.jiig_root_folder,
            sub_task_label=self.sub_task_label,
            tool_name=self.tool_name,
            tool_root_folder=self.tool_root_folder,
            top_task_label=self.top_task_label,
            venv_folder=self.venv_folder,
            version=self.version,
        )
