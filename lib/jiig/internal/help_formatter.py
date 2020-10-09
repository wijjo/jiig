"""Custom help formatting."""

import os
from typing import Text, List, Tuple, Optional, Iterator, Dict

from jiig.task_runner import RunnerHelpFormatter
from jiig.internal import tool_options
from jiig.internal.mapped_task import MappedTask
from jiig.internal.registry import get_tool_tasks
from jiig.utility.general import format_table, make_list


class HelpFormatter(RunnerHelpFormatter):

    def __init__(self, mapped_task: MappedTask = None):
        self.mapped_task = mapped_task

    class HelpTableBuilder:
        def __init__(self):
            self.rows: List[Tuple[Text, Text]] = []
            self.headings: Dict[int, Optional[Text]] = {}

        def start_block(self, heading: Optional[Text] = None):
            self.headings[len(self.rows)] = heading

        def add_row(self, label: Text, comment: Text):
            self.rows.append((label, comment))

        def format_lines(self) -> Iterator[Text]:
            for line_idx, line in enumerate(format_table(*self.rows)):
                if line_idx in self.headings:
                    heading = self.headings.get(line_idx)
                    yield ''
                    if heading:
                        yield f'{heading}:'
                yield f'  {line}'

    def _format_usage(self) -> Iterator[Text]:
        parts: List[Text] = [tool_options.name]
        if not self.mapped_task:
            parts.append('TASK ...')
        else:
            stack_task = self.mapped_task
            command_parts: List[Text] = []
            while stack_task is not None:
                command_parts.insert(0, stack_task.name)
                stack_task = stack_task.parent
            parts.extend(reversed(command_parts))
            if self.mapped_task.options:
                parts.append('[OPTION ...]')
            if self.mapped_task.arguments:
                for arg_data in self.mapped_task.arguments:
                    dest = arg_data.get('dest', '(ARG)')
                    nargs = arg_data.get('nargs')
                    if not nargs or nargs == '?':
                        parts.append(f'[{dest}]')
                    elif nargs == 1 or nargs == '1':
                        parts.append(dest)
                    elif nargs == '*':
                        parts.append(f'[{dest} ...]')
                    else:
                        parts.append(f'{dest} [{dest} ...]')
            if self.mapped_task.sub_tasks:
                parts.append('SUB_TASK ...')
        yield f'Usage: {" ".join(parts)}'

    def _format_description(self) -> Iterator[Text]:
        if not self.mapped_task:
            if tool_options.description:
                yield tool_options.description
        elif self.mapped_task.help:
            yield f'TASK: {self.mapped_task.help}.'

    def _add_table_tasks(self, table_builder: HelpTableBuilder, show_hidden: bool = False):
        # Task list(s)
        if not self.mapped_task:
            # Root task.
            sub_tasks = sorted(get_tool_tasks(include_hidden=show_hidden),
                               key=lambda t: t.name)
            tasks_label = 'TASK'
        else:
            tasks_label = 'SUB_TASK'
            if self.mapped_task.sub_tasks:
                sub_tasks = sorted(self.mapped_task.sub_tasks, key=lambda t: t.name)
            else:
                sub_tasks = None
        if sub_tasks:
            table_builder.start_block(heading=tasks_label)
            primary_tasks = filter(lambda t: t.primary_task, sub_tasks)
            for task in primary_tasks:
                table_builder.add_row(task.name, task.help)
            auxiliary_tasks = filter(lambda t: t.auxiliary_task, sub_tasks)
            if auxiliary_tasks:
                table_builder.start_block()
                for task in auxiliary_tasks:
                    table_builder.add_row(task.name, task.help)
            hidden_tasks = filter(lambda t: t.hidden_task, sub_tasks)
            if show_hidden and hidden_tasks:
                table_builder.start_block()
                for task in hidden_tasks:
                    table_builder.add_row(task.name, task.help)

    def _add_table_positionals(self, table_builder: HelpTableBuilder):
        if self.mapped_task:
            if self.mapped_task.arguments:
                table_builder.start_block(heading='ARGUMENT')
                for arg_dict in self.mapped_task.arguments:
                    table_builder.add_row(arg_dict.get('dest', ''),
                                          arg_dict.get('help', '(no help available)'))

    def _add_table_options(self, table_builder: HelpTableBuilder):
        if self.mapped_task:
            if self.mapped_task.options:
                table_builder.start_block(heading='OPTION')
                for opt_key, opt_dict in self.mapped_task.options.items():
                    table_builder.add_row(', '.join(make_list(opt_key)),
                                          opt_dict.get('help', '(no help available)'))

    def _format_tables(self, show_hidden: bool = False) -> Iterator[Text]:
        table_builder = self.HelpTableBuilder()
        self._add_table_tasks(table_builder, show_hidden=show_hidden)
        self._add_table_positionals(table_builder)
        self._add_table_options(table_builder)
        yield os.linesep.join(table_builder.format_lines())

    def _format_epilog(self) -> Iterator[Text]:
        if self.mapped_task is None:
            # Primary task epilog
            if tool_options.epilog:
                yield tool_options.epilog
        else:
            # Task epilog
            if self.mapped_task.epilog:
                yield self.mapped_task.epilog.strip()
            # Option epilogs.
            for flags, data in self.mapped_task.options.items():
                option_epilog = data.get('epilog', None)
                if option_epilog is not None:
                    option_epilog = option_epilog.strip()
                    if option_epilog:
                        yield f'Option: {", ".join(flags)}{os.linesep}{option_epilog}'
            # Argument epilogs.
            for argument_data in self.mapped_task.arguments:
                argument_epilog = argument_data.get('epilog', None)
                if argument_epilog:
                    dest = argument_data.get('DEST', '(ARG)')
                    yield f'Argument: {dest}{os.linesep}{argument_epilog}'

    def format_help(self, show_hidden: bool = False) -> Text:
        chunks: List[Text] = []

        def _add_block(*chunks_to_add: Optional[Text]):
            for chunk in chunks_to_add:
                chunk = chunk.strip() if chunk else None
                if chunk:
                    if chunks:
                        chunks.append('')
                    chunks.append(chunk)

        _add_block(*self._format_usage())
        _add_block(*self._format_description())
        _add_block(*self._format_tables(show_hidden=show_hidden))
        _add_block(*self._format_epilog())

        return os.linesep.join(chunks)
