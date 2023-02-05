# Copyright (C) 2021-2023, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""Help provider for tool data."""

import os
from dataclasses import dataclass
from typing import Sequence

from jiig.fields import TaskField
from jiig.runtime_task import RuntimeTask, get_task_stack
from jiig.util.default import DefaultValue
from jiig.util.help_formatter import HelpProvider, HelpFormatter
from jiig.util.log import abort
from jiig.util.repetition import Repetition
from jiig.util.text.footnotes import NotesDict, NotesList


@dataclass
class CLIHelpProviderOptions:
    top_task_label: str = 'task'
    sub_task_label: str = 'sub-task'


class CLIHelpProvider(HelpProvider):

    def __init__(self,
                 tool_name: str,
                 tool_description: str,
                 root_task: RuntimeTask,
                 options_by_task: dict[str, dict[str, list[str]]],
                 trailing_by_task: dict[str, str],
                 options: CLIHelpProviderOptions = None,
                 ):
        self.tool_name = tool_name
        self.tool_description = tool_description
        self.root_task = root_task
        self.options_by_task = options_by_task
        self.trailing_by_task = trailing_by_task
        self.options = options or CLIHelpProviderOptions()

    def format_help(self, *names: str, show_hidden: bool = False) -> str:
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

    def format_tool_help(self, show_hidden: bool = False) -> str:
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

    def format_task_help(self, names: Sequence[str], show_hidden: bool = False) -> str:
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
                     tool_name: str,
                     names: Sequence[str],
                     description: str,
                     fields: list[TaskField],
                     sub_tasks: list[RuntimeTask],
                     notes: NotesList,
                     footnotes_list: Sequence[NotesDict],
                     task_label: str,
                     show_hidden: bool,
                     ) -> str:

        formatter = HelpFormatter(tool_name, names, description, task_label)

        # Add notes and footnotes (extra footnotes are only provided for tasks).
        for note in notes:
            formatter.add_note(note)
        for footnotes in footnotes_list:
            formatter.add_footnote_dictionary(footnotes)

        # Add flagged options, if any (tasks only).
        task_receives_trailing = False
        full_name = '.'.join(names)
        options_by_field = self.options_by_task.get(full_name, {})
        for option_field in fields:
            if not task_receives_trailing and full_name in self.trailing_by_task:
                task_receives_trailing = True
            flags = options_by_field.get(option_field.name)
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

        # Add positional arguments.
        for positional_field in fields:
            if positional_field.name not in options_by_field:
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
            sub_task_full_name = '.'.join([full_name, active_sub_task.name])
            sub_task_receives_trailing = bool(
                self.trailing_by_task.get(sub_task_full_name))
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

    def _resolve_task_stack(self, names: Sequence[str]) -> list[RuntimeTask] | None:
        try:
            # Return the stack without the root task.
            return get_task_stack(self.root_task, names)[1:]
        except ValueError as exc:
            abort(str(exc))
