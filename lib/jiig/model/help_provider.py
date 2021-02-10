"""
Help provider for tool data.
"""

import os
from typing import Text, Sequence, List

from jiig import const
from jiig.util.console import log_error, abort
from jiig.util.general import make_list
from jiig.util.help_formatter import HelpProvider, HelpFormatter

from .task import TaskRuntime
from .tool import ToolRuntime


class ToolHelpProvider(HelpProvider):

    def __init__(self, tool: ToolRuntime, root_task: TaskRuntime):
        self.tool = tool
        self.root_task = root_task

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
        formatter = HelpFormatter(self.tool.name,
                                  [],
                                  self.tool.description,
                                  const.TOP_TASK_LABEL)
        for sub_task in self.root_task.sub_tasks:
            formatter.add_command(
                sub_task.name,
                sub_task.description,
                is_secondary=sub_task.visibility == 1,
                is_hidden=sub_task.visibility == 2,
                has_sub_commands=bool(sub_task.sub_tasks),
                receives_trailing_arguments=sub_task.receive_trailing_arguments,
            )
        return formatter.format_help(show_hidden=show_hidden)

    def format_task_help(self, names: Sequence[Text], show_hidden: bool = False) -> Text:
        """
        Populate HelpFormatter with task help data and format help text.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        task_stack = self._get_task_stack(names)

        if not task_stack:
            message = 'No help is available for task command.', ' '.join(names)
            log_error(message)
            return os.linesep.join(['No help is available for task command.',
                                    f'   {" ".join(names)}'])

        active_task = task_stack[-1]

        formatter = HelpFormatter(self.tool.name,
                                  names,
                                  active_task.description,
                                  const.SUB_TASK_LABEL)

        # Add notes and footnotes (extra footnotes are only provided for tasks).
        for note in active_task.notes:
            formatter.add_note(note)
        if self.root_task.footnotes:
            formatter.add_footnote_dictionary(self.root_task.footnotes)
        if active_task.footnotes:
            formatter.add_footnote_dictionary(active_task.footnotes)

        # Add options, if any (tasks only).
        if active_task.flagged_options:
            for opt in active_task.flagged_options:
                formatter.add_option(flags=make_list(opt.flags),
                                     name=opt.name,
                                     description=opt.description,
                                     cardinality=opt.cardinality,
                                     default_value=opt.default_value,
                                     choices=opt.choices,
                                     is_boolean=opt.is_boolean)

        # Add arguments, if any (tasks only).
        if active_task.positional_arguments:
            for arg in active_task.positional_arguments:
                formatter.add_argument(name=arg.name,
                                       description=arg.description,
                                       cardinality=arg.cardinality,
                                       default_value=arg.default_value,
                                       choices=arg.choices)

        # Add help for sub-tasks.
        for active_sub_task in active_task.sub_tasks:
            formatter.add_command(
                active_sub_task.name,
                active_sub_task.description,
                is_secondary=active_sub_task.visibility == 1,
                is_hidden=active_sub_task.visibility == 2,
                has_sub_commands=bool(active_task.sub_tasks),
                receives_trailing_arguments=active_sub_task.receive_trailing_arguments,
            )

        return formatter.format_help(show_hidden=show_hidden)

    def _get_task_stack(self, names: Sequence[Text]) -> List[TaskRuntime]:
        # Resolve the task stack.
        try:
            return self.root_task.get_task_stack(names)
        except ValueError as exc:
            abort(str(exc))
