"""
Tool-related classes.
"""

from dataclasses import dataclass, field
from typing import Text, List, Dict, Union, Type

from jiig.constants import DEFAULT_TEST_FOLDER
from jiig.utility.footnotes import NotesList, NotesDict
from jiig.utility.general import AttrDict
from jiig.utility.help_formatter import HelpProvider


@dataclass
class ToolOptions:
    """Various runtime options used by Tool."""

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

    venv_folder: Text = None
    """Virtual environment root folder - JIIG_VENV_ROOT/<tool> is used if None."""

    venv_enabled: bool = False
    """Enable virtual environment if True."""

    pip_packages: List[Text] = field(default_factory=list)
    """Packages to install in virtual environment, if enabled."""

    library_folders: List[Text] = field(default_factory=list)
    """Library folders to add to Python import path."""

    test_folder: Text = DEFAULT_TEST_FOLDER
    """Test folder path for loading unit tests."""


class Tool:
    """
    Base Tool class.

    If the name is not defined as a sub-class member it will default to the tool
    script name, if available.
    """
    name: Text = None
    """Required name, must be provided by sub-class."""

    description: Text = None
    """Tool description."""

    notes: NotesList = None
    """Tool help notes."""

    footnotes: NotesDict = {}
    """Tool named footnotes that can be referenced by Tool/Task help."""

    tasks: Dict[Text, Union[Type, object]] = {}
    """Task classes or modules by name."""

    secondary_tasks: Dict[Text, Union[Type, object]] = {}
    """Secondary task classes or modules by name."""

    hidden_tasks: Dict[Text, Union[Type, object]] = {}
    """Normally-hidden task classes or modules by name."""

    options: ToolOptions = ToolOptions()
    """Optional tool runtime options."""

    def __init__(self,
                 params: AttrDict,
                 data: object,
                 trailing_arguments: List[Text],
                 help_provider: HelpProvider,
                 ):
        """
        Tool constructor.

        :param params: runtime parameters
        :param data: parsed command line arguments as object with data attributes
        :param trailing_arguments: command line trailing arguments, if requested
        """
        if not self.name:
            raise ValueError('Tool "name" attribute is required.')
        self.params = params
        self.data = data
        self.trailing_arguments = trailing_arguments
        self.help_provider = help_provider

    def on_initialize(self):
        """Optional initialization call-back method."""
        pass

    def on_terminate(self):
        """Optional termination call-back method."""
        pass
