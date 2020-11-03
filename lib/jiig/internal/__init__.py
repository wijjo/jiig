"""Jiig internal types and global data."""

import os
import re
from dataclasses import dataclass, field
from typing import List, Text

from jiig.utility.footnotes import FootnoteDict, NotesList


@dataclass
class _GlobalData:
    """
    Global data.

    * Access through the `global_data` singleton instance! *

    @property is used to limit to attribute style read access. Write access is
    intentionally more awkward and obvious, using "set_...()" methods.
    """

    # Constants and defaults.
    _init_file_name = 'init.jiig'
    _aliases_path = os.path.expanduser('~/.jiig-aliases')
    _template_extension = '.template'
    _template_extension_exe = '.template_exe'
    _template_extension_dot = '.template_dot'
    _templates_folder = 'templates'
    _tool_templates_folder = 'tool-templates'
    _template_folder_symbol_regex = re.compile(r'\(=(\w+)=\)')
    _remote_path_regex = re.compile(r'^([\w\d.@-]+):([\w\d_-~/]+)$')
    _default_test_folder = 'test'
    _cli_dest_name_prefix = 'task'
    _cli_dest_name_separator = '.'
    _cli_metavar_suffix = 'sub_task'
    _cli_metavar_separator = '_'
    _library_folders: List[Text] = field(default_factory=list)
    _debug = False
    _verbose = False
    _dry_run = False

    # --- Read access through public properties.

    @property
    def init_file_name(self) -> Text:
        """Init file name."""
        return self._init_file_name

    @property
    def aliases_path(self) -> Text:
        """Aliases file path."""
        return self._aliases_path

    @property
    def template_extension(self) -> Text:
        """Template file extension."""
        return self._template_extension

    @property
    def template_extension_exe(self) -> Text:
        """Template file extension that adds executable permission."""
        return self._template_extension_exe

    @property
    def template_extension_dot(self) -> Text:
        """Template file extension that prepends '.' to output file."""
        return self._template_extension_dot

    @property
    def all_template_extensions(self) -> List[Text]:
        """All template file extensions."""
        return [self.template_extension,
                self.template_extension_exe,
                self._template_extension_dot]

    @property
    def templates_folder(self) -> Text:
        """General templates folder."""
        return self._templates_folder

    @property
    def tool_templates_folder(self) -> Text:
        """Tool creation templates folder."""
        return self._tool_templates_folder

    @property
    def templates_folder_symbol_regex(self) -> re.Pattern:
        """Regular expression for template file name symbol expansion."""
        return self._template_folder_symbol_regex

    @property
    def remote_path_regex(self) -> re.Pattern:
        """Regular expression for remote path recognition."""
        return self._remote_path_regex

    @property
    def library_folders(self) -> List[Text]:
        """Library folder list."""
        return self._library_folders

    @property
    def default_test_folder(self) -> Text:
        """Default test folder name (if not configured)."""
        return self._default_test_folder

    @property
    def cli_dest_name_prefix(self) -> Text:
        """CLI prefix for dest names."""
        return self._cli_dest_name_prefix

    @property
    def cli_dest_name_separator(self) -> Text:
        """CLI separator for dest names."""
        return self._cli_dest_name_separator

    @property
    def cli_metavar_suffix(self) -> Text:
        """CLI suffix for metavar names."""
        return self._cli_metavar_suffix

    @property
    def cli_metavar_separator(self) -> Text:
        """CLI separator for metavar names."""
        return self._cli_metavar_separator

    @property
    def debug(self) -> bool:
        """Debug mode flag."""
        return self._debug

    @property
    def verbose(self) -> bool:
        """Verbose mode flag."""
        return self._verbose

    @property
    def dry_run(self) -> bool:
        """Dry-run mode flag."""
        return self._dry_run

    # --- Write access through public set... methods.

    # noinspection PyAttributeOutsideInit
    def set_library_folders(self, folders: List[Text]):
        """Set library folder list."""
        self._library_folders = folders

    # noinspection PyAttributeOutsideInit
    def set_debug(self, value: bool):
        """Set debug mode flag."""
        self._debug = value

    # noinspection PyAttributeOutsideInit
    def set_verbose(self, value: bool):
        """Set verbose mode flag."""
        self._verbose = value

    # noinspection PyAttributeOutsideInit
    def set_dry_run(self, value: bool):
        """Set dry-run mode flag."""
        self._dry_run = value


global_data = _GlobalData()


@dataclass
class _ToolOptions:
    """
    Global options that can be configured by the tool as a singleton.

    * Access through the `tool_option` singleton instance! *

    @property is used to limit to attribute style read access. Write access is
    intentionally more awkward and obvious, using "set_...()" methods.
    """

    _name: Text = ''
    _description: Text = ''
    _disable_alias: bool = False
    _disable_help: bool = False
    _disable_debug: bool = False
    _disable_dry_run: bool = False
    _disable_verbose: bool = False
    _notes: NotesList = field(default_factory=list)
    _common_footnotes: FootnoteDict = field(default_factory=dict)

    # --- Read access through public properties.

    @property
    def name(self) -> Text:
        """Tool name."""
        return self._name

    @property
    def description(self) -> Text:
        """Tool description."""
        return self._description

    @property
    def disable_alias(self) -> bool:
        """Aliases are disabled if True."""
        return self._disable_alias

    @property
    def disable_help(self) -> bool:
        """Help is disabled True."""
        return self._disable_help

    @property
    def disable_debug(self) -> bool:
        """Debug mode is disabled if True."""
        return self._disable_debug

    @property
    def disable_dry_run(self) -> bool:
        """Dry-run mode is disabled if True."""
        return self._disable_dry_run

    @property
    def disable_verbose(self) -> bool:
        """Verbose mode is disabled if True."""
        return self._disable_verbose

    @property
    def notes(self) -> NotesList:
        return self._notes

    @property
    def common_footnotes(self) -> FootnoteDict:
        """Dictionary mapping footnote names to text."""
        return self._common_footnotes

    # --- Write access through public set... methods.

    # noinspection PyAttributeOutsideInit
    def set_name(self, value: Text):
        """Set tool name."""
        self._name = value

    # noinspection PyAttributeOutsideInit
    def set_description(self, value: Text):
        """Set tool description."""
        self._description = value

    # noinspection PyAttributeOutsideInit
    def set_disable_alias(self, value: bool):
        """Enable/disable aliases."""
        self._disable_alias = value

    # noinspection PyAttributeOutsideInit
    def set_disable_help(self, value: bool):
        """Enable/disable help."""
        self._disable_help = value

    # noinspection PyAttributeOutsideInit
    def set_disable_debug(self, value: bool):
        """Enable/disable debug mode."""
        self._disable_debug = value

    # noinspection PyAttributeOutsideInit
    def set_disable_dry_run(self, value: bool):
        """Enable/disable dry-run mode."""
        self._disable_dry_run = value

    # noinspection PyAttributeOutsideInit
    def set_disable_verbose(self, value: bool):
        """Enable/disable verbose mode."""
        self._disable_verbose = value

    # noinspection PyAttributeOutsideInit
    def set_notes(self, value: NotesList):
        """Set tool footnote dictionary."""
        self._notes = value

    # noinspection PyAttributeOutsideInit
    def set_common_footnotes(self, value: FootnoteDict):
        """Set tool footnote dictionary."""
        self._common_footnotes = value


tool_options = _ToolOptions()
