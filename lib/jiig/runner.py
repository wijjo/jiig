from __future__ import annotations
import os
from typing import Dict, Text, Optional, Any, Callable

from . import utility


class HelpFormatter:
    """Abstract help formatter."""
    def format_help(self) -> Text:
        raise NotImplementedError


class RunnerData:
    """Results returned after parsing the command line."""
    def __init__(self, args: Any, help_formatters: Dict[Text, HelpFormatter], **params):
        self.args = args
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
        self.params = utility.AttrDict(data.params)
        self.help_formatters = data.help_formatters

    # === Public methods.

    def format_help(self, *task_names: Text):
        dest_name = utility.make_dest_name(*task_names)
        help_formatter = self.help_formatters.get(dest_name, None)
        if not help_formatter:
            utility.display_error(f'No help available for: {" ".join(task_names)}')
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

    @classmethod
    def create_runner(cls, data: RunnerData) -> TaskRunner:
        return RUNNER_FACTORY(data) if RUNNER_FACTORY else cls(data)


# Runner factory registered by @runner_factory decorator. Last registered one wins.
RunnerFactoryFunction = Callable[[RunnerData], TaskRunner]
RUNNER_FACTORY: Optional[RunnerFactoryFunction] = None


def runner_factory() -> Callable[[RunnerFactoryFunction], RunnerFactoryFunction]:
    """Decorator for custom runner factories."""
    def inner(function: RunnerFactoryFunction) -> RunnerFactoryFunction:
        global RUNNER_FACTORY
        RUNNER_FACTORY = function
        return function
    return inner
