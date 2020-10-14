"""Custom help formatting."""

import os
from dataclasses import dataclass
from shutil import get_terminal_size
from textwrap import wrap
from typing import Text, List, Tuple, Optional, Iterator, Dict

from jiig.internal import OptionDict, ArgumentList, NotesList
from jiig.utility.footnotes import FootnoteDict, FootnoteBuilder
from jiig.utility.general import format_table, make_list


class Footnote:
    def __init__(self, text: Text):
        self.text = text.strip()
        self.option_flags: List[Text] = []
        self.argument_dests: List[Text] = []


class HelpTaskVisibility:
    NORMAL = 0
    AUXILIARY = 1
    HIDDEN = 2


@dataclass
class HelpSubTaskData:
    name: Text
    visibility: int
    help_text: Text


HELP_TABLE_INDENT_SIZE = 2
HELP_MINIMUM_WRAP_WIDTH = 40


class HelpFormatter:

    def __init__(self,
                 task_type_label: Text,
                 command_names: List[Text],
                 description: Text,
                 sub_tasks: List[HelpSubTaskData] = None,
                 options: OptionDict = None,
                 arguments: ArgumentList = None,
                 notes: NotesList = None,
                 footnote_dictionaries: List[Optional[FootnoteDict]] = None):
        """
        Help formatter constructor.

        :param task_type_label: task type label, e.g. 'TASK' or 'SUB_TASK'
        :param command_names: command names in appearance order for Usage
        :param sub_tasks: sub-task data, i.e. name/visibility/help text
        :param description: task description for description block
        :param options: task options
        :param arguments: task arguments
        :param footnote_dictionaries: dictionaries for resolving footnote references
        """
        self.task_type_label = task_type_label
        self.command_names = command_names
        self.sub_tasks = sub_tasks
        self.description = description
        self.options = options
        self.arguments = arguments
        self.notes = notes
        self.footnote_builder = FootnoteBuilder()
        if footnote_dictionaries:
            self.footnote_builder.add_footnotes(*footnote_dictionaries)

    class TableFormatter:
        def __init__(self, max_width: int):
            self.max_width = max_width
            self.rows: List[Tuple[Text, Text]] = []
            self.headings: Dict[int, Optional[Text]] = {}

        def start_block(self, heading: Optional[Text] = None):
            self.headings[len(self.rows)] = heading

        def add_row(self, label: Text, comment: Text):
            self.rows.append((label, comment))

        def format_lines(self) -> Iterator[Text]:
            for line_idx, line in enumerate(
                    format_table(*self.rows, max_width=self.max_width)):
                if line_idx in self.headings:
                    heading = self.headings.get(line_idx)
                    yield ''
                    if heading:
                        yield f'{heading}:'
                yield f'{" " * HELP_TABLE_INDENT_SIZE}{line}'

    def _format_usage(self) -> Iterator[Text]:
        parts: List[Text] = ['Usage:']
        parts.extend(self.command_names)
        if self.options:
            parts.append('[OPTION ...]')
        if self.arguments:
            for arg_data in self.arguments:
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
        parts.extend([self.task_type_label, '...'])
        yield ' '.join(parts)

    def _format_help_text(self, help_text: Optional[Text]) -> Text:
        help_text = help_text.strip() if help_text else ''
        if not help_text:
            return '(no help available)'
        return self.footnote_builder.scan_text(help_text)

    def _format_description(self) -> Iterator[Text]:
        yield self._format_help_text(self.description)

    def _add_table_tasks(self,
                         table_builder: TableFormatter,
                         show_hidden: bool = False
                         ):
        # Task list(s)
        if self.sub_tasks:
            table_builder.start_block(heading=self.task_type_label)
            primary_tasks = filter(
                lambda st: st.visibility == HelpTaskVisibility.NORMAL,
                self.sub_tasks)
            for task in primary_tasks:
                table_builder.add_row(task.name,
                                      self._format_help_text(task.help_text))
            auxiliary_tasks = filter(
                lambda st: st.visibility == HelpTaskVisibility.AUXILIARY,
                self.sub_tasks)
            if auxiliary_tasks:
                table_builder.start_block()
                for task in auxiliary_tasks:
                    table_builder.add_row(task.name,
                                          self._format_help_text(task.help_text))
            hidden_tasks = filter(
                lambda st: st.visibility == HelpTaskVisibility.HIDDEN,
                self.sub_tasks)
            if show_hidden and hidden_tasks:
                table_builder.start_block()
                for task in hidden_tasks:
                    table_builder.add_row(task.name,
                                          self._format_help_text(task.help_text))

    def _add_table_positionals(self, table_builder: TableFormatter):
        if self.arguments:
            table_builder.start_block(heading='ARGUMENT')
            for arg_dict in self.arguments:
                table_builder.add_row(arg_dict.get('dest', ''),
                                      self._format_help_text(arg_dict.get('help')))

    def _add_table_options(self, table_builder: TableFormatter):
        if self.options:
            table_builder.start_block(heading='OPTION')
            for opt_key, opt_dict in self.options.items():
                table_builder.add_row(', '.join(make_list(opt_key)),
                                      self._format_help_text(opt_dict.get('help')))

    def _format_tables(self, show_hidden: bool, width: int) -> Iterator[Text]:
        table_builder = self.TableFormatter(width)
        self._add_table_tasks(table_builder, show_hidden=show_hidden)
        self._add_table_positionals(table_builder)
        self._add_table_options(table_builder)
        yield os.linesep.join(table_builder.format_lines())

    def _format_epilog(self, max_width: int) -> Text:
        def _format_text(text_block: Optional[Text]) -> Text:
            if text_block is None:
                return ''
            return os.linesep.join(wrap(text_block, width=max_width))
        if self.notes:
            for note in self.notes:
                yield _format_text(note)
        for footnote_text in self.footnote_builder.format_footnotes():
            yield _format_text(footnote_text)

    class OutputFormatter:
        def __init__(self):
            self.chunks: List[Text] = []

        def add_block(self, *chunks_to_add: Optional[Text]):
            for chunk in chunks_to_add:
                chunk = chunk.strip() if chunk else None
                if chunk:
                    if self.chunks:
                        self.chunks.append('')
                    self.chunks.append(chunk)

        def format_help(self) -> Text:
            return os.linesep.join(self.chunks)

    def format_help(self, show_hidden: bool = False) -> Text:
        terminal_size = get_terminal_size()
        max_width = max(HELP_MINIMUM_WRAP_WIDTH,
                        terminal_size.columns - HELP_TABLE_INDENT_SIZE)
        builder = self.OutputFormatter()
        builder.add_block(*self._format_usage())
        builder.add_block(*self._format_description())
        builder.add_block(*self._format_tables(show_hidden, max_width))
        builder.add_block(*self._format_epilog(max_width))
        return builder.format_help()
