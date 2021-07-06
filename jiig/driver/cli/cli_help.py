"""Help provider for tool data."""

import os
from dataclasses import dataclass, field
from typing import Text, Sequence, List, Optional

from ...util.log import abort
from ...util.footnotes import NotesDict, NotesList
from ...util.general import DefaultValue
from ...util.repetition import Repetition
from ...util.help_formatter import HelpProvider, HelpFormatter

from ..driver_task import DriverTask, DriverField

from .cli_hints import CLI_HINT_FLAGS, CLI_HINT_TRAILING
from .global_options import GLOBAL_OPTIONS


@dataclass
class CLIHelpProviderOptions:
    top_task_label: Text = 'task'
    sub_task_label: Text = 'sub-task'
    supported_global_options: List[Text] = field(default_factory=list)


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
        return self._format_help(self.tool_name,
                                 [],
                                 self.tool_description,
                                 self.root_task.fields,
                                 self.root_task.sub_tasks,
                                 self.root_task.notes,
                                 [self.root_task.footnotes],
                                 self.options.top_task_label,
                                 show_hidden,
                                 )

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

        return self._format_help(self.tool_name,
                                 names,
                                 active_task.description,
                                 active_task.fields,
                                 active_task.sub_tasks,
                                 active_task.notes,
                                 [self.root_task.footnotes, active_task.footnotes],
                                 self.options.sub_task_label,
                                 show_hidden,
                                 )

    def _format_help(self,
                     tool_name: Text,
                     names: Sequence[Text],
                     description: Text,
                     fields: List[DriverField],
                     sub_tasks: List[DriverTask],
                     notes: NotesList,
                     footnotes_list: Sequence[NotesDict],
                     task_label: Text,
                     show_hidden: bool,
                     ) -> Text:

        formatter = HelpFormatter(tool_name, names, description, task_label)

        # Add notes and footnotes (extra footnotes are only provided for tasks).
        for note in notes:
            formatter.add_note(note)
        for footnotes in footnotes_list:
            formatter.add_footnote_dictionary(footnotes)

        # Add flagged options, if any (tasks only).
        task_receives_trailing = False
        for option_field in fields:
            if not task_receives_trailing and option_field.hints.get(CLI_HINT_TRAILING):
                task_receives_trailing = True
            flags = option_field.hints.get(CLI_HINT_FLAGS)
            if flags is not None:
                if option_field.repeat is None:
                    repeat = None
                else:
                    repeat = Repetition(option_field.repeat.minimum, option_field.repeat.maximum)
                if option_field.default is None:
                    default = None
                else:
                    default = DefaultValue(option_field.default.value)
                formatter.add_option(flags=flags,
                                     name=option_field.name,
                                     description=option_field.description,
                                     repeat=repeat,
                                     default=default,
                                     choices=option_field.choices,
                                     is_boolean=option_field.element_type is bool)
        # Add global options only when displaying top level help.
        if not names:
            for global_option in GLOBAL_OPTIONS:
                if global_option.name in self.options.supported_global_options:
                    formatter.add_option(flags=global_option.flags,
                                         name=global_option.name,
                                         description=global_option.description,
                                         is_boolean=True)

        # Add positional arguments.
        for positional_field in fields:
            if positional_field.hints.get(CLI_HINT_FLAGS) is None:
                if positional_field.repeat is None:
                    repeat = None
                else:
                    repeat = Repetition(positional_field.repeat.minimum,
                                        positional_field.repeat.maximum)
                if positional_field.default is None:
                    default = None
                else:
                    default = DefaultValue(positional_field.default.value)
                formatter.add_argument(name=positional_field.name,
                                       description=positional_field.description,
                                       repeat=repeat,
                                       default=default,
                                       choices=positional_field.choices)

        # Add help for sub-tasks.
        for active_sub_task in sorted(sub_tasks, key=lambda t: t.name):
            sub_task_receives_trailing = False
            for sub_task_field in active_sub_task.fields:
                if not sub_task_receives_trailing and sub_task_field.hints.get(CLI_HINT_TRAILING):
                    sub_task_receives_trailing = True
            if show_hidden or active_sub_task.visibility != 2:
                formatter.add_command(
                    active_sub_task.name,
                    active_sub_task.description,
                    is_secondary=active_sub_task.visibility == 1,
                    is_hidden=active_sub_task.visibility == 2,
                    has_sub_commands=bool(active_sub_task.sub_tasks),
                    receives_trailing_arguments=sub_task_receives_trailing,
                )

        return formatter.format_help(receives_trailing_arguments=task_receives_trailing)

    def _resolve_task_stack(self, names: Sequence[Text]) -> Optional[List[DriverTask]]:
        try:
            return self.root_task.resolve_task_stack(names)
        except ValueError as exc:
            abort(str(exc))
