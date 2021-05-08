"""Help provider for tool data."""

import os
from dataclasses import dataclass
from typing import Text, Sequence, List, Optional

from jiig.util.console import abort
from jiig.util.general import DefaultValue
from jiig.util.repetition import Repetition
from jiig.util.help_formatter import HelpProvider, HelpFormatter

from ..driver_task import DriverTask

from .cli_hints import CLI_HINT_FLAGS, CLI_HINT_TRAILING


@dataclass
class CLIHelpProviderOptions:
    top_task_label: Text = 'task'
    sub_task_label: Text = 'sub-task'


class CLIHelpProvider(HelpProvider):

    def __init__(self,
                 tool_name: Text,
                 tool_description: Text,
                 root_task: DriverTask,
                 options: CLIHelpProviderOptions = None):
        self.tool_name = tool_name
        self.tool_description = tool_description
        self.root_task = root_task
        self.options = options or CLIHelpProviderOptions()

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

    def format_tool_help(self, show_hidden: bool = False) -> Text:
        """
        Use HelpFormatter to format tool help text.

        :param show_hidden: show hidden task help if True
        """
        formatter = HelpFormatter(self.tool_name,
                                  [],
                                  self.tool_description,
                                  self.options.top_task_label)
        for sub_task in sorted(self.root_task.sub_tasks, key=lambda t: t.name):
            receives_trailing_arguments = task_receives_trailing_arguments(sub_task)
            formatter.add_command(
                sub_task.name,
                sub_task.description,
                is_secondary=sub_task.visibility == 1,
                is_hidden=sub_task.visibility == 2,
                has_sub_commands=bool(sub_task.sub_tasks),
                receives_trailing_arguments=receives_trailing_arguments,
            )
        return formatter.format_help(show_hidden=show_hidden)

    def format_task_help(self, names: Sequence[Text], show_hidden: bool = False) -> Text:
        """
        Populate HelpFormatter with task help data and format help text.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        task_stack = self._resolve_task_stack(names)

        if not task_stack:
            return os.linesep.join(['No help is available for unknown command.',
                                    f'   {" ".join(names)}'])

        active_task = task_stack[-1]

        formatter = HelpFormatter(self.tool_name,
                                  names,
                                  active_task.description,
                                  self.options.sub_task_label)

        # Add notes and footnotes (extra footnotes are only provided for tasks).
        for note in active_task.notes:
            formatter.add_note(note)
        if self.root_task.footnotes:
            formatter.add_footnote_dictionary(self.root_task.footnotes)
        if active_task.footnotes:
            formatter.add_footnote_dictionary(active_task.footnotes)

        # Add flagged options, if any (tasks only).
        for field in active_task.fields:
            flags = field.hints.get(CLI_HINT_FLAGS)
            if flags is not None:
                if field.repeat is None:
                    repeat = None
                else:
                    repeat = Repetition(field.repeat.minimum, field.repeat.maximum)
                if field.default is None:
                    default = None
                else:
                    default = DefaultValue(field.default.value)
                formatter.add_option(flags=flags,
                                     name=field.name,
                                     description=field.description,
                                     repeat=repeat,
                                     default=default,
                                     choices=field.choices,
                                     is_boolean=field.element_type is bool)

        # Add positional arguments, if any (tasks only).
        for field in active_task.fields:
            if field.hints.get(CLI_HINT_FLAGS) is None:
                if field.repeat is None:
                    repeat = None
                else:
                    repeat = Repetition(field.repeat.minimum, field.repeat.maximum)
                if field.default is None:
                    default = None
                else:
                    default = DefaultValue(field.default.value)
                formatter.add_argument(name=field.name,
                                       description=field.description,
                                       repeat=repeat,
                                       default=default,
                                       choices=field.choices)

        # Add help for sub-tasks.
        for active_sub_task in sorted(active_task.sub_tasks, key=lambda t: t.name):
            receives_trailing_arguments = task_receives_trailing_arguments(active_sub_task)
            formatter.add_command(
                active_sub_task.name,
                active_sub_task.description,
                is_secondary=active_sub_task.visibility == 1,
                is_hidden=active_sub_task.visibility == 2,
                has_sub_commands=bool(active_sub_task.sub_tasks),
                receives_trailing_arguments=receives_trailing_arguments,
            )

        receives_trailing_arguments = task_receives_trailing_arguments(active_task)
        return formatter.format_help(show_hidden=show_hidden,
                                     receives_trailing_arguments=receives_trailing_arguments)

    def _resolve_task_stack(self, names: Sequence[Text]) -> Optional[List[DriverTask]]:
        try:
            return self.root_task.resolve_task_stack(names)
        except ValueError as exc:
            abort(str(exc))


def task_receives_trailing_arguments(task: DriverTask) -> bool:
    """
    Check field hints to see if task requires trailing arguments.

    :param task: task with fields to check
    :return: True if a task field needs trailing arguments
    """
    for field in task.fields:
        if field.hints.get(CLI_HINT_TRAILING):
            return True
    return False
