"""
Task runner.

Object passed to task functions for task execution.
"""

import os
from typing import Dict, Text, Any, List, Callable

from jiig.internal.globals import global_data
from jiig.internal.help_formatter import HelpFormatter
from jiig.utility.cli import make_dest_name
from jiig.utility.console import log_error
from jiig.utility.general import AttrDict


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
        # Make global flags available to applications.
        self.debug = global_data.debug
        self.dry_run = global_data.dry_run
        self.verbose = global_data.verbose


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

    def format_help(self, *task_names: Text, show_hidden: bool = False):
        dest_name = make_dest_name(*task_names)
        help_formatter = self.help_formatters.get(dest_name, None)
        if not help_formatter:
            log_error(f'No help available for: {" ".join(task_names)}')
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


TaskFunction = Callable[[TaskRunner], None]
TaskFunctionsSpec = List[TaskFunction]
RunnerFactoryFunction = Callable[[RunnerData], TaskRunner]
