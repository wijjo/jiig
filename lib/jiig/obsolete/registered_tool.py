"""
RegisteredTool wraps a tool class and adds finalized data.

Registration basically takes an input Tool class and massages the data for
consumption by the runtime engine. It adds some data, converts Tool/Task module
references to Tool/Task class references, and finalizes options, paths, etc..
"""

import os
from copy import copy
from typing import Text, Optional, List, Dict, Sequence

from jiig import const
from jiig.util.console import log_error, abort
from jiig.util.general import make_list, plural
from jiig.util.help_formatter import HelpFormatter, HelpProvider
from jiig.util.process import shell_quote_arg

from .registered_task import RegisteredTask
from jiig.model.app_runtime import AppRuntime
from jiig.config.task import Task
from jiig.config.tool import Tool


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
    def __init__(self, tool: Tool):
        self.tool = tool

        # Use a root task to hold the sub-task tree.
        class RootTask(Task):
            name = '_root_'
            tasks = self.tool.tasks
            secondary_tasks = self.tool.secondary_tasks
            hidden_tasks = self.tool.hidden_tasks

            def on_run(self):
                pass

        self.root_task = RegisteredTask(RootTask, False, False)

        super().__init__()

    def run(self,
            names: List[Text],
            runtime_options: AppRuntime,
            data: object,
            trailing_args: List[Text],
            cli_args: List[Text],
            ):
        """
        Create a Tool instance, execute its tasks, and invoke all hooks.

        :param names: task name stack for execution
        :param runtime_options: runtime options
        :param data: parsed command line arguments as object with data attributes
        :param trailing_args: command line trailing arguments, if requested
        :param cli_args: full list of command line arguments
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
            # Update the Tool with CLI data/trailing arguments and a HelpProvider (this class).
            self.tool.data = data
            self.tool.trailing_arguments = trailing_args
            self.tool.help_provider = self

            # Invoke the tool initialization hook.
            self.tool.on_init()

            # Run task stack in top to bottom order.
            for task_idx, registered_task in enumerate(registered_task_stack):
                task_name = names[task_idx]
                task_instance = registered_task.create_task(task_name,
                                                            self.configuration,
                                                            runtime_options,
                                                            prepared_data,
                                                            trailing_args,
                                                            self)
                # Invoke the task run hook.
                task_instance.on_run()

            # Invoke the tool termination hook.
            self.tool.on_exit()
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
            task_container = registered_task.tasks
        return registered_task_stack

    def format_tool_help(self, show_hidden: bool = False) -> Text:
        """
        Use HelpFormatter to format tool help text.

        :param show_hidden: show hidden task help if True
        """
        formatter = HelpFormatter(self.configuration.name,
                                  [],
                                  self.description,
                                  const.TOP_TASK_LABEL)
        for name, registered_task in self.tasks.items():
            formatter.add_command(
                name,
                registered_task.description,
                is_secondary=registered_task.is_secondary,
                is_hidden=registered_task.is_hidden,
                has_sub_commands=bool(registered_task.sub_tasks),
                receives_trailing_arguments=registered_task.options.receive_trailing_arguments,
            )
        return formatter.format_help(show_hidden=show_hidden)

    def get_pip_packages(self, *names: Text) -> List[Text]:
        """
        Look up required Pip packages for tool and tasks (based on names provided).

        :param names: task name stack
        :return: the Pip packages required by the tool and tasks provided
        """
        pip_packages: List[Text] = copy(self.configuration.pip_packages)
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

        formatter = HelpFormatter(self.configuration.name,
                                  names,
                                  registered_task.description,
                                  const.SUB_TASK_LABEL)

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
            formatter.add_command(
                name,
                registered_task.description,
                is_secondary=registered_task.is_secondary,
                is_hidden=registered_task.is_hidden,
                has_sub_commands=bool(registered_task.tasks),
                receives_trailing_arguments=registered_task.options.receive_trailing_arguments,
            )

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
