"""
Runner provides data and an API to task call-back functions..
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Text, List, Optional, Iterator

from jiig.util.alias_catalog import AliasCatalog, open_alias_catalog
from jiig.util.help_formatter import HelpProvider

from .tool import ToolRuntime


@dataclass
class Runner:
    """Application runtime data and options."""

    tool: ToolRuntime
    """Tool runtime data."""

    trailing_arguments: List[Text]
    """Trailing command line arguments, if required."""

    help_provider: HelpProvider
    """Help provider for providing input data for help text."""

    is_secondary: bool
    """True if the current task is secondary, i.e. a dependency or parent task."""

    debug: bool
    """True if debugging mode is in effect."""

    dry_run: bool
    """True if performing a non-destructive dry run."""

    verbose: bool
    """True if displaying verbose messages."""

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
        Expands string template against symbols from configuration and more_params.

        :param text: input string to expand
        :param more_params: additional dictionary to use for expansion
        :return: expanded string
        """
        return text.format(**self.tool.expansion_symbols, **more_params)

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
    def open_alias_catalog(self) -> Iterator[AliasCatalog]:
        """
        Open alias catalog.

        For use in a `with` block to automatically close the catalog.

        :return: catalog
        """
        with open_alias_catalog(self.tool.name, self.tool.aliases_path) as catalog:
            yield catalog
