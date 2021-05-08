"""
Runner provides data and an API to task call-back functions..
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Text, Iterator

from jiig.driver import Driver, DriverTask
from jiig.util.alias_catalog import AliasCatalog, open_alias_catalog
from jiig.util.console import abort

from .runtime_task import RuntimeTask
from .runtime_tool import RuntimeTool


@dataclass
class Runtime:
    """Application runtime data and options."""

    tool: RuntimeTool
    """Tool runtime data."""

    root_task: RuntimeTask
    """Active root task."""

    driver_root_task: DriverTask
    """Active root task used by driver."""

    driver: Driver
    """Active Jiig interface driver."""

    is_secondary: bool
    """True if the current task is secondary, i.e. a dependency or parent task."""

    debug: bool
    """True if debugging mode is in effect."""

    dry_run: bool
    """True if performing a non-destructive dry run."""

    verbose: bool
    """True if displaying verbose messages."""

    def expand_string(self, text: Text, **more_params) -> Text:
        """
        Expands string template against symbols from configuration and more_params.

        :param text: input string to expand
        :param more_params: additional dictionary to use for expansion
        :return: expanded string
        """
        try:
            return text.format(**self.tool.expansion_symbols, **more_params)
        except KeyError as exc:
            abort('Failed to expand template string.', text, exc)

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

    def provide_help(self, *names: Text, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        self.driver.provide_help(self.driver_root_task, *names, show_hidden=show_hidden)
