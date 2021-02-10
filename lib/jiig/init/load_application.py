"""
Command line argument parsing.
"""

from dataclasses import dataclass
from typing import Text, List

from jiig import cli, const, model
from jiig.util.alias_catalog import expand_alias_name, open_alias_catalog
from jiig.util.console import abort
from jiig.util.general import make_list, plural
from jiig.util.process import shell_quote_arg

from .pre_load import AppPreLoadData


@dataclass
class ApplicationData:
    """Application runtime data and options."""

    runner: model.Runner
    """Runner API for task call-backs."""

    root_task: model.TaskRuntime
    """Root task."""

    active_task_stack: List[model.TaskRuntime]
    """Active (running) task stack."""

    data: object
    """Data from parsed command line arguments."""

    @property
    def active_names(self) -> List[Text]:
        """
        Provide active task stack names.

        :return: active name list
        """
        return [sub_task.name for sub_task in self.active_task_stack]


def _resolve_root_task(tool: model.ToolRuntime) -> model.TaskRuntime:
    # Note that sub_tasks are only resolved as needed by TaskRuntime, since not
    # all task pathways need to be traversed in most cases.
    root_task = model.TaskRuntime.resolve_task_spec(tool.root_task_spec, '(root)', 2)
    if root_task is None:
        abort('Failed to resolve root task.')
    return root_task


def _add_sub_task_arguments_and_subcommands(command: cli.ParserCommand,
                                            sub_task: model.TaskRuntime):
    for opt in sub_task.flagged_options:
        command.add_option(opt.name,
                           opt.description,
                           make_list(opt.flags),
                           is_boolean=opt.is_boolean,
                           cardinality=opt.cardinality,
                           default_value=opt.default_value,
                           choices=opt.choices)
    for arg in sub_task.positional_arguments:
        command.add_positional_argument(arg.name,
                                        arg.description or '(no description)',
                                        cardinality=arg.cardinality,
                                        default_value=arg.default_value,
                                        choices=arg.choices)
    for sub_sub_task in sub_task.sub_tasks:
        sub_command = command.add_sub_command(sub_sub_task.name,
                                              sub_sub_task.description)
        _add_sub_task_arguments_and_subcommands(sub_command, sub_sub_task)


def _check_trailing_arguments(active_sub_task: model.TaskRuntime,
                              names: List[Text],
                              trailing_args: List[Text],
                              cli_args: List[Text],
                              ):
    expect_trailing_arguments = active_sub_task.receive_trailing_arguments
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


def _finalize_arguments(trailing_arguments: List[Text],
                        tool: model.ToolRuntime,
                        ) -> List[Text]:
    # Build the final arguments list, expanding an alias as required.
    if not trailing_arguments:
        final_arguments: List[Text] = []
    elif not expand_alias_name(trailing_arguments[0]):
        final_arguments = trailing_arguments
    else:
        with open_alias_catalog(tool.name,
                                const.DEFAULT_ALIASES_PATH) as catalog:
            alias = catalog.get_alias(trailing_arguments[0])
            if not alias:
                abort(f'Alias "{trailing_arguments[0]}" not found.')
            final_arguments = alias.command + trailing_arguments[1:]
    return final_arguments


def _get_task_stack(root_task: model.TaskRuntime,
                    names: List[Text],
                    ) -> List[model.TaskRuntime]:
    # Resolve the task stack.
    try:
        return root_task.get_task_stack(names)
    except ValueError as exc:
        abort(str(exc))


def go(pre_load_data: AppPreLoadData,
       tool: model.ToolRuntime,
       ) -> ApplicationData:
    """
    Parse the command line.

    :param pre_load_data: interpreter data, including CLI options and arguments
    :param tool: tool configuration
    :return: final runtime data passed along to running tasks
    """
    # Expand alias as needed to produce final argument list.
    final_arguments = _finalize_arguments(pre_load_data.trailing_arguments, tool)

    # Resolve the root task.
    root_task = _resolve_root_task(tool)

    # Create and initialize the parser driver.
    parser_driver = cli.get_parser_driver(
        tool.name,
        tool.description,
        implementation=pre_load_data.parser_implementation,
        disable_debug=tool.options.disable_debug,
        disable_dry_run=tool.options.disable_dry_run,
        disable_verbose=tool.options.disable_verbose)
    root_parser = parser_driver.initialize_parser()
    for sub_task in root_task.sub_tasks:
        command = root_parser.add_command(sub_task.name, sub_task.description)
        _add_sub_task_arguments_and_subcommands(command, sub_task)

    # Parse the command line.
    parse_results = parser_driver.parse(final_arguments, capture_trailing=True)

    # Resolve the task stack based on the command name list.
    active_sub_task_stack = _get_task_stack(root_task, parse_results.names)

    # Shouldn't have trailing arguments unless the specific command needs it.
    _check_trailing_arguments(active_sub_task_stack[-1],
                              parse_results.names,
                              parse_results.trailing_arguments,
                              final_arguments)

    runner = model.Runner(tool=tool,
                          trailing_arguments=parse_results.trailing_arguments,
                          help_provider=model.ToolHelpProvider(tool, root_task),
                          is_secondary=False,
                          debug=pre_load_data.debug,
                          dry_run=pre_load_data.dry_run,
                          verbose=pre_load_data.verbose)

    return ApplicationData(runner, root_task, active_sub_task_stack, parse_results.data)
