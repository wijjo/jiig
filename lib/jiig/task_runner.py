"""
Task runner.

Object passed to task functions for task execution.
"""

from __future__ import annotations

import os
from typing import Dict, Text, Any, List

from jiig.internal import global_data
from jiig.utility.cli import make_dest_name
from jiig.utility.console import log_error
from jiig.utility.general import AttrDict


class AbstractHelpFormatter:
    """Abstract help formatter."""
    def format_help(self) -> Text:
        raise NotImplementedError


class RunnerData:
    """Results returned after parsing the command line."""
    def __init__(self,
                 args: Any,
                 trailing_args: List[Text],
                 help_formatters: Dict[Text, AbstractHelpFormatter],
                 params: Dict):
        self.args = args
        self.trailing_args = trailing_args
        self.help_formatters = help_formatters
        self.params = params
        # Make global flags available to applications.
        self.debug = global_data.DEBUG
        self.dry_run = global_data.DRY_RUN
        self.verbose = global_data.VERBOSE


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
        self.debug = data.debug
        self.dry_run = data.dry_run
        self.verbose = data.verbose

    # === Public methods.

    def format_help(self, *task_names: Text):
        dest_name = make_dest_name(*task_names)
        help_formatter = self.help_formatters.get(dest_name, None)
        if not help_formatter:
            log_error(f'No help available for: {" ".join(task_names)}')
            return None
        return help_formatter.format_help()

    def expand_string(self, text: Text, **more_params) -> Text:
        """Expands string template against symbols from self.params and more_params."""
        return text.format(**self.params, **more_params)

    def expand_path_template(self, path: Text, **more_params) -> Text:
        """Calls expand_string() after fixing slashes, as needed."""
        if os.path.sep != '/':
            path = path.replace('/', os.path.sep)
        return self.expand_string(path, **more_params)
