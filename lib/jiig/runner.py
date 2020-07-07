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

    def get_primary_task_folder(self):
        for task_folder in self.params.TASK_FOLDERS:
            if task_folder.startswith(self.params.BASE_FOLDER):
                return task_folder
        utility.abort('Could not determine primary task folder.')


# Runner factory registered by @runner_factory decorator. Last registered one wins.
RunnerFactoryFunction = Callable[[RunnerData], TaskRunner]
RUNNER_FACTORY: Optional[RunnerFactoryFunction] = None


def runner_factory() -> Callable[[RunnerFactoryFunction], RunnerFactoryFunction]:
    def inner(function: RunnerFactoryFunction) -> RunnerFactoryFunction:
        global RUNNER_FACTORY
        RUNNER_FACTORY = function
        return function
    return inner
