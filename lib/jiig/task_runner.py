"""
Task runner.

Object passed to task functions for task execution.
"""

import os
from contextlib import contextmanager
from typing import Dict, Text, Any, List, Iterator

from jiig.utility import alias_catalog
from jiig.utility.console import log_error, log_message
from jiig.utility.general import AttrDict
from jiig.utility.help_formatter import HelpFormatter


class RunnerData:
    """Results returned after parsing the command line."""
    def __init__(self,
                 args: Any,
                 trailing_args: List[Text],
                 help_formatters: Dict[Text, HelpFormatter],
                 params: Dict):
        self.args = args
        self.trailing_args = trailing_args
        self.help_formatters = help_formatters
        self.params = params


class TaskRunner:
    """
    Task runner.

    Supplied to task functions to provide command line options and arguments.
    Also offers an API that supports common required functionality.
    """

    # === Construction.

    def __init__(self, data: RunnerData):
        # Parsers are needed only for help formatting.
        self.args = data.args
        self.trailing_args = data.trailing_args
        self.params = AttrDict(data.params)
        self.help_formatters = data.help_formatters

    # === Public methods.

    def format_help(self, *task_names: Text, show_hidden: bool = False):
        task_full_name = self.params.FULL_NAME_SEPARATOR.join(task_names)
        help_formatter = self.help_formatters.get(task_full_name, None)
        if not help_formatter:
            log_error(f'No help available for "{task_full_name}".')
            if self.params.VERBOSE:
                full_names = [f'"{key.replace(self.params.FULL_NAME_SEPARATOR, " ")}"'
                              for key in self.help_formatters.keys()]
                log_message(f'Available help:', *full_names)
            return None
        return help_formatter.format_help(show_hidden=show_hidden)

    def expand_string(self, text: Text, **more_params) -> Text:
        """Expands string template against symbols from self.params and more_params."""
        return text.format(**self.params, **more_params)

    def expand_path_template(self, path: Text, **more_params) -> Text:
        """Calls expand_string() after fixing slashes, as needed."""
        if os.path.sep != '/':
            path = path.replace('/', os.path.sep)
        return self.expand_string(path, **more_params)

    @contextmanager
    def open_alias_catalog(self) -> Iterator[alias_catalog.AliasCatalog]:
        with alias_catalog.open_alias_catalog(
                self.params.TOOL_NAME,
                self.params.ALIASES_PATH) as catalog:
            yield catalog
