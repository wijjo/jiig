import os
from typing import Dict, Text, Optional, Any, Callable

from . import constants, utility, configuration_file


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
        self._local_configuration: Optional[utility.AttrDict] = None

    # === Public methods.

    def has_application(self) -> bool:
        return hasattr(self.args, 'APP_FOLDER')

    @property
    def app_folder(self) -> Text:
        if not hasattr(self.args, 'APP_FOLDER') or not self.args.APP_FOLDER:
            utility.abort('No APP_FOLDER argument was provided by the Task.')
        return os.path.realpath(self.args.APP_FOLDER)

    @property
    def configuration_path(self) -> Text:
        file_name = self.params.APP_NAME + constants.CONFIGURATION_EXTENSION
        return os.path.join(self.app_folder, file_name)

    @property
    def local_configuration_path(self) -> Text:
        file_name = (self.params.APP_NAME +
                     constants.LOCAL_CONFIGURATION_SUFFIX +
                     constants.CONFIGURATION_EXTENSION)
        return os.path.join(self.app_folder, file_name)

    def virtual_environment_program(self, name: Text) -> Text:
        return os.path.join(self.params.VENV_FOLDER, 'bin', name)

    def get_flask_app_string(self) -> Text:
        config_path = getattr(self.args, 'CONFIG_PATH', None)
        if config_path:
            add_arg_text = ', config_path="{}"'.format(config_path)
        else:
            add_arg_text = ''
        return '{}.app:create_app("{}"{})'.format(
            self.params.APP_NAME, self.app_folder, add_arg_text)

    @property
    def local_configuration(self) -> utility.AttrDict:
        if self._local_configuration is None:
            config_path = utility.short_path(self.local_configuration_path)
            if not os.path.exists(config_path):
                utility.abort('Local configuration file does not exist.',
                              path=config_path)
            utility.display_message('Load local configuration file.',
                                    path=config_path)
            try:
                self._local_configuration = utility.AttrDict(
                    configuration_file.for_file(self.local_configuration_path).load())
            except configuration_file.ConfigurationError as exc:
                utility.abort('Unable to read local configuration file.',
                              config_path=config_path, exception=exc)
        return self._local_configuration

    def clear_local_configuration(self):
        self._local_configuration = None

    def format_help(self, *task_names: Text):
        dest_name = utility.make_dest_name(*task_names)
        help_formatter = self.help_formatters.get(dest_name, None)
        if not help_formatter:
            utility.display_error(f'No help available for: {" ".join(task_names)}')
            return None
        return help_formatter.format_help()


# Runner factory registered by @runner_factory decorator. Last registered one wins.
RunnerFactoryFunction = Callable[[RunnerData], TaskRunner]
RUNNER_FACTORY: Optional[RunnerFactoryFunction] = None


def runner_factory() -> Callable[[RunnerFactoryFunction], RunnerFactoryFunction]:
    def inner(function: RunnerFactoryFunction) -> RunnerFactoryFunction:
        global RUNNER_FACTORY
        RUNNER_FACTORY = function
        return function
    return inner
