"""
Task class.

The Task class has raw data, as extracted from task modules or or user-defined
task classes. It should not be altered at runtime.
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Text, List, Iterator, Optional, Dict, Union, Type, Tuple

from jiig.utility import alias_catalog
from jiig.utility.footnotes import NotesList, NotesDict
from jiig.utility.general import AttrDict
from jiig.utility.help_formatter import HelpProvider


@dataclass
class TaskOptions:
    pip_packages: List[Text] = field(default_factory=list)
    """Pip-installed packages required from a virtual environment, if enabled."""

    receive_trailing_arguments: bool = False
    """Keep unparsed trailing arguments if True."""


class Task:
    """
    Base Task class.

    Note that Task names are set on the instance by the constructor, because the
    name comes from task/sub-task dictionary keys.

    # Argument dictionaries.

    Maps argument <identifier> keys to <specification> values.

    ## <identifier>

    format: "<name><modifier>"

    The modifier is optional.

    Supported modifiers are:
    - "[<repetition>]": allowed repetition as a number, '*', or '+'
    - "?": indicates an optional (single) positional argument
    - "!": specifies a boolean flag option that will be True when present

    When a repetition modifier is specified argument data is provided as a list.

    ## <specification>

    The argument specification value can either be a string or a tuple.

    A string becomes the argument description, and the argument is configured as
    a simple text string.

    A tuple supports the following content to provide greater flexibility in
    defining arguments.

    - "-..." strings are taken as option flags. Without any flag strings, it is
      assumed to be a positional argument.
    - Any other text string is taken as the argument description.
    - Callable references are taken as argument data adapters.
    - A Choices object can define a limited value set for the argument.
    - A Default object can establish a default value if the argument is not
      provided on the command line.
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

    args: Dict[Text, Union[Text, Tuple]] = {}
    """Argument/option definition dictionary."""

    options: TaskOptions = TaskOptions()
    """Optional task runtime options."""

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
