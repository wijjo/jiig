import os
from contextlib import contextmanager
from typing import Dict, Text, Optional, List, Any

from . import constants, utility, configuration_file


class HelpFormatter:
    """Abstract help formatter."""
    def format_help(self) -> Text:
        raise NotImplementedError


class TaskRunner:
    """
    Task runner.

    Supplied to task functions to provide command line options and arguments.
    Also offers an API that supports common required functionality.
    """

    # === Construction.

    def __init__(self, args: Any, help_formatters: Dict[Text, HelpFormatter], **params):
        # Parsers are needed only for help formatting.
        self.args = args
        self.params = utility.AttrDict(params)
        self.help_formatters = help_formatters
        self._local_configuration: Optional[utility.AttrDict] = None

    # === Public utility methods.

    @staticmethod
    def phase(name):
        utility.display_phase(name)

    def message(self, text, **kwargs):
        verbose = kwargs.pop('verbose', False)
        if verbose and not (self.args.VERBOSE or self.args.DRY_RUN):
            return
        utility.display_message(text, **kwargs)

    @staticmethod
    def warning(text, **kwargs):
        utility.display_warning(text, **kwargs)

    @staticmethod
    def error(text, **kwargs):
        utility.display_error(text, **kwargs)

    @staticmethod
    def abort(text, **kwargs):
        if 'skip' not in kwargs:
            kwargs['skip'] = 1      # Don't display this method in a stack trace.
        utility.abort(text, **kwargs)

    @staticmethod
    @contextmanager
    def chdir(folder):
        with utility.chdir(folder) as restore_folder:
            yield restore_folder

    def run(self,
            cmd_args: List[Text],
            unchecked: bool = False,
            replace_process: bool = False,
            working_folder: Text = None,
            env: Dict = None):
        return utility.run(
            cmd_args,
            unchecked=unchecked,
            replace_process=replace_process,
            working_folder=working_folder,
            env=env,
            dry_run=self.args.DRY_RUN)

    def run_remote(self,
                   host: Text,
                   cmd_args: List[Text],
                   unchecked: bool = False,
                   replace_process: bool = False):
        return utility.run(cmd_args,
                           host=host,
                           unchecked=unchecked,
                           replace_process=replace_process,
                           dry_run=self.args.DRY_RUN)

    def run_shell(self,
                  cmd_args: List[Text],
                  unchecked: bool = False,
                  working_folder: Text = None,
                  replace_process: bool = False):
        return utility.run(cmd_args,
                           unchecked=unchecked,
                           replace_process=replace_process,
                           working_folder=working_folder,
                           shell=True,
                           dry_run=self.args.DRY_RUN)

    @staticmethod
    def curl(url: Text):
        """Download from a URL and return a CurlResponse object."""
        return utility.curl(url)

    def delete_folder(self, path: Text, quiet: bool = False):
        utility.delete_folder(path,
                              quiet=quiet,
                              dry_run=self.args.DRY_RUN)

    def delete_file(self, path: Text, quiet: bool = False):
        utility.delete_file(path,
                            quiet=quiet,
                            dry_run=self.args.DRY_RUN)

    def create_folder(self, path: Text, keep: bool = False, quiet: bool = False):
        utility.create_folder(path,
                              keep=keep,
                              quiet=quiet,
                              dry_run=self.args.DRY_RUN)

    def copy_folder(self,
                    src_path: Text,
                    dst_path: Text,
                    merge: bool = False,
                    quiet: bool = False):
        utility.copy_folder(src_path,
                            dst_path,
                            merge=merge,
                            quiet=quiet,
                            dry_run=self.args.DRY_RUN)

    def move_file(self,
                  src_path: Text,
                  dst_path: Text,
                  overwrite: bool = False,
                  quiet: bool = False):
        utility.move_file(src_path,
                          dst_path,
                          overwrite=overwrite,
                          quiet=quiet,
                          dry_run=self.args.DRY_RUN)

    def move_folder(self,
                    src_path: Text,
                    dst_path: Text,
                    overwrite: bool = False,
                    quiet: bool = False):
        utility.move_folder(src_path,
                            dst_path,
                            overwrite=overwrite,
                            quiet=quiet,
                            dry_run=self.args.DRY_RUN)

    def copy_files(self,
                   src_glob: Text,
                   dst_path: Text,
                   allow_empty: bool = False,
                   quiet: bool = False):
        utility.copy_files(src_glob,
                           dst_path,
                           allow_empty=allow_empty,
                           quiet=quiet,
                           dry_run=self.args.DRY_RUN)

    def sync_folders(self,
                     src_folder: Text,
                     dst_folder: Text,
                     exclude: List = None,
                     check_contents: bool = False,
                     quiet: bool = False):
        utility.sync_folders(src_folder,
                             dst_folder,
                             exclude=exclude,
                             check_contents=check_contents,
                             quiet=quiet,
                             dry_run=self.args.DRY_RUN)

    def expand_template(self,
                        source_path: Text,
                        target_path: Text,
                        overwrite: bool = False,
                        executable: bool = False,
                        symbols: Dict = None):
        utility.expand_template(source_path,
                                target_path,
                                overwrite=overwrite,
                                executable=executable,
                                symbols=symbols,
                                dry_run=self.args.DRY_RUN)

    # === Public methods.

    def has_application(self) -> bool:
        return hasattr(self.args, 'APP_FOLDER')

    @property
    def app_folder(self) -> Text:
        if not hasattr(self.args, 'APP_FOLDER') or not self.args.APP_FOLDER:
            self.abort('No APP_FOLDER argument was provided by the Task.')
        return os.path.realpath(self.args.APP_FOLDER)

    @property
    def configuration_path(self) -> Text:
        file_name = self.params.APP_NAME + constants.Jiig.configuration_extension
        return os.path.join(self.app_folder, file_name)

    @property
    def local_configuration_path(self) -> Text:
        file_name = (self.params.APP_NAME +
                     constants.Jiig.local_configuration_suffix +
                     constants.Jiig.configuration_extension)
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
                self.abort('Local configuration file does not exist.',
                           path=config_path)
            self.message('Load local configuration file.',
                         path=config_path)
            try:
                self._local_configuration = utility.AttrDict(
                    configuration_file.for_file(self.local_configuration_path).load())
            except configuration_file.ConfigurationError as exc:
                self.abort('Unable to read local configuration file.',
                           config_path=config_path, exception=exc)
        return self._local_configuration

    def clear_local_configuration(self):
        self._local_configuration = None

    def format_help(self, *task_names: Text):
        dest_name = utility.make_dest_name(*task_names)
        help_formatter = self.help_formatters.get(dest_name, None)
        if not help_formatter:
            self.error(f'No help available for: {" ".join(task_names)}')
            return None
        return help_formatter.format_help()
