"""
Tool registration class.
"""

from typing import Text, List, Dict, Union, Type

from jiig.util.footnotes import NotesList, NotesDict
from jiig.util.help_formatter import HelpProvider

from .tool_configuration import ToolConfiguration
from .runtime_options import RuntimeOptions


class Tool:
    """
    Base Tool class.

    Holds a good deal of meta-data that is used by features like the Pdoc3
    documentation generator to minimize the need for separate configurations.
    """
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

    def __init__(self,
                 configuration: ToolConfiguration,
                 runtime_options: RuntimeOptions,
                 data: object,
                 trailing_arguments: List[Text],
                 help_provider: HelpProvider,
                 ):
        """
        Tool constructor.

        :param configuration: tool configuration data
        :param runtime_options: runtime optionsÅÅ
        :param data: parsed command line arguments as object with data attributes
        :param trailing_arguments: command line trailing arguments, if requested
        :param help_provider: interface for providing data to HelpFormatter
        """
        self.configuration = configuration
        self.runtime = runtime_options
        self.data = data
        self.trailing_arguments = trailing_arguments
        self.help_provider = help_provider

    def on_initialize(self):
        """Optional initialization call-back method."""
        pass

    def on_terminate(self):
        """Optional termination call-back method."""
        pass
