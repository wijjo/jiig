"""
RegisteredTool wraps a tool class and adds finalized data.

Registration basically takes an input Tool class and massages the data for
consumption by the runtime engine. It adds some data, converts Tool/Task module
references to Tool/Task class references, and finalizes options, paths, etc..
"""

import os
from copy import copy
from typing import Type, Text, Optional, List, Dict, Sequence

from jiig import constants
from jiig.utility.console import log_error, abort
from jiig.utility.general import make_list, AttrDict, plural
from jiig.utility.help_formatter import HelpFormatter, HelpProvider
from jiig.utility.process import shell_quote_arg

from .registered_tasks import RegisteredTask, prepare_registered_text
from .tasks import Task
from .tools import ToolOptions, Tool


class ArgumentNameError(RuntimeError):
    pass


class ArgumentData:
    """A blank object that receives argument data as attributes."""

    def __getattr__(self, name):
        """
        Provide a better error for bad attribute names.

        :param name: attribute name
        :return: attribute value
        """
        if name not in self.__dict__:
            raise ArgumentNameError(f'Command argument data has no "{name}" attribute.')
        return super().__getattr__(name)


class RegisteredTool(HelpProvider):
    """
    A registered Tool class and associated data.

    Presents normalized and finalized runtime data based on a Tool class.
    """
    def __init__(self, tool_class: Type[Tool]):
        text_results = prepare_registered_text(tool_class.description,
                                               tool_class.notes,
                                               getattr(tool_class, '__doc__', None))
        self.tool_name = tool_class.name
        self.description = text_results.description
        self.project = tool_class.project or self.tool_name.capitalize()
        self.version = tool_class.version or '(no version)'
        self.copyright = tool_class.copyright or '(no copyright)'
        self.author = tool_class.author or '(author)'
        self.notes = text_results.notes
        self.options = self._prepare_registered_tool_options(tool_class)
        self.footnotes = tool_class.footnotes
        # Used by run() method.
        self._tool_class = tool_class

        # Use a root task to hold the sub-task tree.
        class RootTask(Task):
            name = '_root_'
            sub_tasks = tool_class.tasks
            secondary_sub_tasks = tool_class.secondary_tasks
            hidden_sub_tasks = tool_class.hidden_tasks

            def on_run(self):
                pass

        self.root_task = RegisteredTask(RootTask, False, False)

        super().__init__()

    def run(self,
            names: List[Text],
            data: object,
            trailing_args: List[Text],
            cli_args: List[Text],
            **params
            ):
        """
        Create a Tool instance, execute its tasks, and invoke all hooks.

        :param names: task name stack for execution
        :param data: parsed command line arguments as object with data attributes
        :param trailing_args: command line trailing arguments, if requested
        :param cli_args: full list of command line arguments
        :param params: runtime parameter dictionary (converted to AttrDict)
        :return:
        """
        registered_task_stack = self.get_task_stack(*names)
        if registered_task_stack is None:
            abort('Task class not found for command.', ' '.join(names))

        # Shouldn't have trailing arguments unless the specific command needs it.
        registered_task = registered_task_stack[-1]
        self._check_trailing_arguments(registered_task, names, trailing_args, cli_args)

        # Prepare argument data using raw data and task option/argument definitions.
        prepared_data = ArgumentData()
        errors: List[Text] = []
        for registered_task in registered_task_stack:
            results = registered_task.prepare_argument_data(data, prepared_data)
            errors.extend(results.errors)
        if len(errors) > 0:
            abort(f'{len(errors)} argument failure(s):', *errors)

        try:
            # Add params not provided by caller.
            run_params = AttrDict(params,
                                  ALIASES_PATH=constants.ALIASES_PATH,
                                  AUTHOR=self.author,
                                  COPYRIGHT=self.copyright,
                                  DEFAULT_build_FOLDER=constants.DEFAULT_BUILD_FOLDER,
                                  DEFAULT_DOC_FOLDER=constants.DEFAULT_DOC_FOLDER,
                                  DEFAULT_TEST_FOLDER=constants.DEFAULT_TEST_FOLDER,
                                  FULL_NAME_SEPARATOR=constants.FULL_NAME_SEPARATOR,
                                  JIIG_TEMPLATES_FOLDER=constants.JIIG_TEMPLATES_FOLDER,
                                  PIP_PACKAGES=self.options.pip_packages,
                                  PROJECT=self.project,
                                  SUB_TASK_LABEL=constants.SUB_TASK_LABEL,
                                  TASK_TEMPLATES_FOLDER=constants.TASK_TEMPLATES_FOLDER,
                                  DOC_FOLDER=self.options.doc_folder,
                                  BUILD_FOLDER=self.options.build_folder,
                                  TOOL_TEMPLATES_FOLDER=constants.TOOL_TEMPLATES_FOLDER,
                                  TOOL_TEST_FOLDER=self.options.test_folder,
                                  TOP_TASK_LABEL=constants.TOP_TASK_LABEL,
                                  VENV_SUPPORT=self.options.venv_support,
                                  VENV_FOLDER=self.options.venv_folder,
                                  VERSION=self.version,
                                  )

            # Create the tool instance (self serves as the HelpProvider used for tool help).
            tool = self._tool_class(run_params,
                                    data,
                                    trailing_args,
                                    self)

            # Invoke the tool initialization hook.
            tool.on_initialize()

            # Run task stack in top to bottom order.
            for task_idx, registered_task in enumerate(registered_task_stack):
                task_name = names[task_idx]
                task_instance = registered_task.create_task(task_name,
                                                            run_params,
                                                            prepared_data,
                                                            trailing_args,
                                                            self)
                # Invoke the task run hook.
                task_instance.on_run()

            # Invoke the tool termination hook.
            tool.on_terminate()
        except KeyboardInterrupt:
            print('')
        except ArgumentNameError as exc:
            abort(str(exc))
        except Exception as exc:
            abort(f'Task command failed:', ' '.join(names), exc)

    def get_task_stack(self, *names: Text) -> Optional[List[RegisteredTask]]:
        """
        Provide stack of registered tasks given a task name sequence.

        :param names: task names
        :return: registered task stack (list) or None if it failed to register
        """
        registered_task_stack: List[RegisteredTask] = []
        task_container = self.tasks
        for name in names:
            registered_task = task_container.get(name)
            if registered_task is None:
                return None
            registered_task_stack.append(registered_task)
            task_container = registered_task.sub_tasks
        return registered_task_stack

    def format_tool_help(self, show_hidden: bool = False) -> Text:
        """
        Use HelpFormatter to format tool help text.

        :param show_hidden: show hidden task help if True
        """
        formatter = HelpFormatter(self.tool_name,
                                  [],
                                  self.description,
                                  constants.TOP_TASK_LABEL)
        for name, registered_task in self.tasks.items():
            formatter.add_command(name,
                                  registered_task.description,
                                  is_secondary=registered_task.is_secondary,
                                  is_hidden=registered_task.is_hidden,
                                  has_sub_commands=bool(registered_task.sub_tasks))
        return formatter.format_help(show_hidden=show_hidden)

    def get_pip_packages(self, *names: Text) -> List[Text]:
        """
        Look up required Pip packages for tool and tasks (based on names provided).

        :param names: task name stack
        :return: the Pip packages required by the tool and tasks provided
        """
        pip_packages: List[Text] = copy(self.options.pip_packages)
        registered_task_stack = self.get_task_stack(*names)
        if registered_task_stack:
            for registered_task in registered_task_stack:
                for pip_package in registered_task.options.pip_packages:
                    if pip_package not in pip_packages:
                        pip_packages.append(pip_package)
        return pip_packages

    def format_task_help(self, names: Sequence[Text], show_hidden: bool = False) -> Text:
        """
        Populate HelpFormatter with task help data and format help text.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        registered_task_stack = self.get_task_stack(*names)

        if not registered_task_stack:
            message = 'No help is available for task command.', ' '.join(names)
            log_error(message)
            return os.linesep.join(['No help is available for task command.',
                                    f'   {" ".join(names)}'])

        registered_task = registered_task_stack[-1]

        formatter = HelpFormatter(self.tool_name,
                                  names,
                                  registered_task.description,
                                  constants.SUB_TASK_LABEL)

        # Add notes and footnotes (extra footnotes are only provided for tasks).
        for note in registered_task.notes:
            formatter.add_note(note)
        if self.footnotes:
            formatter.add_footnote_dictionary(self.footnotes)
        if registered_task.footnotes:
            formatter.add_footnote_dictionary(registered_task.footnotes)

        # Add options, if any (tasks only).
        if registered_task.opts:
            for opt in registered_task.opts:
                formatter.add_option(flags=make_list(opt.flags),
                                     name=opt.name,
                                     description=opt.description,
                                     cardinality=opt.cardinality,
                                     default_value=opt.default_value,
                                     choices=opt.choices,
                                     is_boolean=opt.is_boolean)

        # Add arguments, if any (tasks only).
        if registered_task.args:
            for arg in registered_task.args:
                formatter.add_argument(name=arg.name,
                                       description=arg.description,
                                       cardinality=arg.cardinality,
                                       default_value=arg.default_value,
                                       choices=arg.choices)

        # Add help for sub-tasks.
        for name, registered_task in registered_task.sub_tasks.items():
            formatter.add_command(name,
                                  registered_task.description,
                                  is_secondary=registered_task.is_secondary,
                                  is_hidden=registered_task.is_hidden,
                                  has_sub_commands=bool(registered_task.sub_tasks))

        return formatter.format_help(show_hidden=show_hidden)

    def format_help(self, *names: Text, show_hidden: bool = False) -> Text:
        """
        Format help.

        Required HelpProvider override called by help-related tasks.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        :return: formatted help text
        """
        if names:
            return self.format_task_help(names, show_hidden=show_hidden)
        else:
            return self.format_tool_help(show_hidden=show_hidden)

    @property
    def tasks(self) -> Dict[Text, RegisteredTask]:
        """
        Access root task sub-tasks.

        :return: root sub-tasks dictionary
        """
        return self.root_task.sub_tasks

    @staticmethod
    def _prepare_registered_tool_options(source_tool_class: Type[Tool]) -> ToolOptions:
        # Make a fresh copy of options with minor updates for paths.
        venv_folder = source_tool_class.options.venv_folder
        if venv_folder is None:
            venv_folder = os.path.join(constants.JIIG_VENV_ROOT, source_tool_class.name)
        test_folder = source_tool_class.options.test_folder
        if test_folder is None:
            test_folder = constants.DEFAULT_TEST_FOLDER
        doc_folder = source_tool_class.options.doc_folder
        if doc_folder is None:
            doc_folder = constants.DEFAULT_DOC_FOLDER
        build_folder = source_tool_class.options.build_folder
        if build_folder is None:
            build_folder = constants.DEFAULT_BUILD_FOLDER
        return ToolOptions(
            disable_alias=source_tool_class.options.disable_alias,
            disable_help=source_tool_class.options.disable_help,
            disable_debug=source_tool_class.options.disable_debug,
            disable_dry_run=source_tool_class.options.disable_dry_run,
            disable_verbose=source_tool_class.options.disable_verbose,
            venv_folder=os.path.realpath(venv_folder),
            venv_support=source_tool_class.options.venv_support,
            pip_packages=copy(source_tool_class.options.pip_packages),
            library_folders=copy(source_tool_class.options.library_folders),
            test_folder=os.path.realpath(test_folder),
            doc_folder=os.path.realpath(doc_folder),
            build_folder=os.path.realpath(build_folder),
        )

    @staticmethod
    def _check_trailing_arguments(registered_task: RegisteredTask,
                                  names: List[Text],
                                  trailing_args: List[Text],
                                  cli_args: List[Text],
                                  ):
        expect_trailing_arguments = registered_task.options.receive_trailing_arguments
        if trailing_args and not expect_trailing_arguments:
            # Build quoted command arguments and caret markers for error arguments.
            args_in = names + trailing_args
            args_out: List[Text] = []
            markers: List[Text] = []
            arg_in_idx = 0
            for cli_arg in cli_args:
                quoted_arg = shell_quote_arg(cli_arg)
                args_out.append(quoted_arg)
                marker = ' '
                if arg_in_idx < len(args_in) and cli_arg == args_in[arg_in_idx]:
                    if arg_in_idx >= len(names):
                        marker = '^'
                    arg_in_idx += 1
                markers.append(marker * len(quoted_arg))
            abort(f'Bad command {plural("argument", trailing_args)}.',
                  ' '.join(cli_args),
                  ' '.join(markers))
