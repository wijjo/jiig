"""
Load tool and retrieve registry data
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Text, Iterator

from jiig import registry
from jiig.utility.console import abort
from jiig.utility.general import make_list
from jiig.utility.footnotes import NoteDict, NotesList
from jiig.utility.help_formatter import HelpFormatter, HelpArgument, HelpSubTaskData
from jiig.utility.stream import open_text

from .parameters_initializer import ParameterData


@dataclass
class ToolData:
    all_tasks: List[registry.RegisteredTask]
    tasks_by_name: Dict[Text, registry.RegisteredTask]
    capture_trailing: bool
    help_formatters: Dict[Text, HelpFormatter]
    name: Text
    description: Text
    disable_alias: bool
    disable_help: bool
    disable_debug: bool
    disable_dry_run: bool
    disable_verbose: bool
    notes: NotesList
    footnotes: NoteDict


def _get_top_level_sub_tasks_help(all_tasks: List[registry.RegisteredTask],
                                  ) -> Iterator[HelpSubTaskData]:
    for task in filter(lambda t: t.parent is None, all_tasks):
        yield HelpSubTaskData(task.name, task.help_visibility, task.description)


def _get_task_sub_tasks_help(registered_task: registry.RegisteredTask,
                             ) -> Iterator[HelpSubTaskData]:
    for sub_task in sorted(registered_task.sub_tasks, key=lambda task: task.name):
        yield HelpSubTaskData(sub_task.name, sub_task.help_visibility, sub_task.description)


def _get_task_arguments_help(registered_task: registry.RegisteredTask,
                             ) -> Iterator[HelpArgument]:
    for argument in sorted(registered_task.arguments, key=lambda arg: arg.name):
        yield HelpArgument(argument.name,
                           argument.description,
                           argument.cardinality,
                           make_list(argument.flags),
                           argument.default_value,
                           argument.choices)


def _build_formatters_dictionary(all_tasks: List[registry.RegisteredTask],
                                 tool_description: Text,
                                 tool_notes: NotesList,
                                 tool_footnotes: NoteDict,
                                 param_data: ParameterData,
                                 ) -> Dict[Text, HelpFormatter]:
    formatters = {
        '': HelpFormatter(
            param_data.top_task_label,
            [],
            tool_description,
            sub_tasks=list(_get_top_level_sub_tasks_help(all_tasks)),
            notes=tool_notes,
            footnote_dictionaries=[tool_footnotes],
        ),
    }

    def _add_task_help_recursive(registered_task: registry.RegisteredTask,
                                 names: List[Text] = None,
                                 ):
        names = names or []
        task_names = names + [registered_task.name]
        task_full_name = param_data.full_name_separator.join(task_names)
        formatters[task_full_name] = HelpFormatter(
            param_data.sub_task_label,
            task_names,
            registered_task.description,
            sub_tasks=list(_get_task_sub_tasks_help(registered_task)),
            arguments=list(_get_task_arguments_help(registered_task)),
            notes=registered_task.notes,
            footnote_dictionaries=[tool_footnotes, registered_task.footnotes]
        )

        for sub_task in registered_task.sub_tasks:
            _add_task_help_recursive(sub_task, names=names + [registered_task.name])

    for task in all_tasks:
        _add_task_help_recursive(task)

    return formatters


def initialize(param_data: ParameterData) -> ToolData:
    """
    Load the tool script and post-process global tool options.

    :param param_data: data from preliminary command line processing
    """
    try:
        # Execute the tool script to trigger task registration.
        script_symbols = {}
        with open_text(file=param_data.tool_script_path) as text_stream:
            exec(text_stream.read(), script_symbols)

        registered_tool = registry.get_tool()

        # If no name was provided use the script base name.
        tool_name = registered_tool.name
        if not tool_name:
            tool_name = os.path.basename(param_data.tool_script_path)

        # If no description was provided use the doc string or provide a default.
        tool_description = registered_tool.description
        if not tool_description:
            tool_description = script_symbols.get('__doc__', '').strip()
        if not tool_description:
            tool_description = '(no description)'

        # Load standard modules, if enabled.
        if not registered_tool.disable_help:
            import jiig.tasks.help      # noqa
        if not registered_tool.disable_alias:
            import jiig.tasks.alias     # noqa
        all_tasks = registry.api.get_sorted_tasks()
        capture_trailing = False
        if param_data.raw_arguments:
            top_task = registry.api.get_task_by_name(
                param_data.raw_arguments[0])
            if top_task:
                capture_trailing = top_task.capture_trailing_arguments
        help_formatters = _build_formatters_dictionary(all_tasks,
                                                       tool_description,
                                                       registered_tool.notes,
                                                       registered_tool.footnotes,
                                                       param_data)

        return ToolData(all_tasks=all_tasks,
                        tasks_by_name=registry.api.get_tasks_by_name(),
                        capture_trailing=capture_trailing,
                        help_formatters=help_formatters,
                        name=tool_name,
                        description=tool_description,
                        disable_alias=registered_tool.disable_alias,
                        disable_help=registered_tool.disable_help,
                        disable_debug=registered_tool.disable_debug,
                        disable_dry_run=registered_tool.disable_dry_run,
                        disable_verbose=registered_tool.disable_verbose,
                        notes=registered_tool.notes,
                        footnotes=registered_tool.footnotes)

    except Exception as exc:
        abort('Exception occurred while loading tool.', exception=exc)
