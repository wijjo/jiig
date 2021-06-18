"""
Registered tool.
"""

import os
import sys
from typing import List, Text, Optional, Dict, Any

from jiig.registry import TaskReference, Tool, ToolOptions, JIIG_VENV_ROOT


class RuntimeTool:
    """
    Wraps Tool configuration object to present final tool level runtime data.

    Cleans up and digests raw Tool specification for what is needed at runtime.

    @property methods enforce read-only access to unmodified Tool data.
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
            self._jiig_root_folder = self._jiig_library_folder
        # Make `library_folders` a complete list of all needed paths.
        # Include tool and jiig library paths.
        self._library_folders: List[Text] = self._tool.library_folders or []
        if not self._library_folders:
            self._library_folders.append(self.tool_root_folder)
        if self.jiig_library_folder not in self._library_folders:
            self._library_folders.append(self.jiig_library_folder)
        if self._tool.project_name is not None:
            self._project_name = self._tool.project_name
        else:
            self._project_name = self._tool.tool_name.capitalize()
        if self._tool.venv_folder is not None:
            self._venv_folder = self._tool.venv_folder
        else:
            self._venv_folder = os.path.join(os.path.expanduser(JIIG_VENV_ROOT),
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
    def root_task_reference(self) -> TaskReference:
        """
        Root task reference.

        :return: root task reference, as class, module name, or module
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
        return self._tool.tool_options

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
    def venv_interpreter(self) -> Text:
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
        return self.pip_packages or self.options.venv_required

    @property
    def version(self) -> Text:
        """
        Tool version identifier.

        :return: version label
        """
        return self._tool.version
