"""
Task class.

The Task class has raw data, as extracted from task modules or or user-defined
task classes. It should not be altered at runtime.
"""

import os
from contextlib import contextmanager
from typing import Text, List, Iterator, Optional, Dict, Union, Type

from jiig.utility import alias_catalog
from jiig.utility.footnotes import NotesList, NotesDict
from jiig.utility.general import AttrDict
from jiig.utility.help_formatter import HelpProvider

from .arguments import Arg, Opt


class Task:
    """
    Base Task class.

    Note that Task names are set on the instance by the constructor, because the
    name comes from task/sub-task dictionary keys.
    """

    description: Text = None
    """Task description."""

    notes: NotesList = None
    """Task help notes."""

    footnotes: NotesDict = {}
    """Named footnotes displayed in task help if referenced by "[<name>]"."""

    sub_tasks: Dict[Text, Union[Type, object]] = {}
    """Sub-task classes or modules by name."""

    secondary_sub_tasks: Dict[Text, Union[Type, object]] = {}
    """Secondary sub-task classes or modules by name."""

    hidden_sub_tasks: Dict[Text, Union[Type, object]] = {}
    """Normally-hidden sub-task classes or modules by name."""

    opts: List[Opt] = []
    """Option definition list."""

    args: List[Arg] = []
    """Argument definition list."""

    receive_trailing_arguments: bool = False
    """Keep unparsed trailing arguments if True."""

    def __init__(self,
                 name: Text,
                 params: AttrDict,
                 data: object,
                 trailing_arguments: List[Text],
                 help_provider: HelpProvider):
        """
        Task constructor.

        :param name: required name
        :param params: configuration parameter data
        :param data: parsed command line arguments as object with data attributes
        :param trailing_arguments: command line trailing arguments, if requested
        :param help_provider: used for displaying help
        """
        assert name
        self.name = name
        self.params = params
        self.data = data
        self.trailing_arguments = trailing_arguments
        self.help_provider = help_provider

    def on_run(self):
        """Optional task execution call-back method."""
        raise NotImplementedError

    def format_help(self, *task_names: Text, show_hidden: bool = False) -> Optional[Text]:
        """
        Format task help.

        :param task_names: task name parts (name stack)
        :param show_hidden: show hidden tasks if True
        :return: formatted help text
        """
        return self.help_provider.format_help(*task_names, show_hidden=show_hidden)

    def expand_string(self, text: Text, **more_params) -> Text:
        """
        Expands string template against symbols from self.params and more_params.

        :param text: input string to expand
        :param more_params: additional dictionary to use for expansion
        :return: expanded string
        """
        return text.format(**self.params, **more_params)

    def expand_path_template(self, path: Text, **more_params) -> Text:
        """
        Calls expand_string() after fixing slashes, as needed.

        :param path: input path to expand
        :param more_params: additional dictionary to use for expansion
        :return: expanded path string
        """
        if os.path.sep != '/':
            path = path.replace('/', os.path.sep)
        return self.expand_string(path, **more_params)

    @contextmanager
    def open_alias_catalog(self) -> Iterator[alias_catalog.AliasCatalog]:
        """
        Open alias catalog.

        For use in a `with` block to automatically close the catalog.

        :return: catalog
        """
        with alias_catalog.open_alias_catalog(
                self.params.TOOL_NAME,
                self.params.ALIASES_PATH) as catalog:
            yield catalog
