# Copyright (C) 2020-2023, Steven Cooper
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

"""Custom help formatting."""

import os
from dataclasses import dataclass
from shutil import get_terminal_size
from textwrap import wrap
from typing import Iterator, Sequence, Any

from .collections import make_list
from .default import DefaultValue
from jiig.util.text.footnotes import FootnoteBuilder, NotesList, NotesDict
from .repetition import Repetition


class Footnote:
    """Footnote data."""
    def __init__(self, text: str):
        """
        Footnote constructor.

        :param text: footnote text
        """
        self.text = text.strip()
        self.option_flags: list[str] = []
        self.argument_dests: list[str] = []


@dataclass
class HelpCommandData:
    """Help data for command."""
    name: str
    help_text: str
    is_secondary: bool = False
    is_hidden: bool = False
    has_sub_commands: bool = False
    receives_trailing_arguments: bool = False


@dataclass
class HelpOption:
    """Help data for option."""
    name: str
    description: str = None
    flags: list[str] = None
    repeat: Repetition = None
    default: DefaultValue = None
    choices: Sequence = None
    is_boolean: bool = False

    def __post_init__(self):
        self.name = self.name.upper()


@dataclass
class HelpArgument:
    """Help data for argument."""
    name: str
    description: str = None
    repeat: Repetition = None
    default: DefaultValue = None
    choices: Sequence = None

    def __post_init__(self):
        self.name = self.name.upper()


HELP_TABLE_INDENT_SIZE = 2
HELP_MINIMUM_WRAP_WIDTH = 40
HELP_LEFT_COLUMN_MAX_WIDTH = 20


@dataclass
class _HelpLabeledListItem:
    label: str
    text: str


class _HelpLabeledListFormatter:

    labeled_list_separator = '  '

    def __init__(self,
                 label_max_width: int,
                 line_max_width: int,
                 ):
        self.label_max_width = label_max_width
        self.line_max_width = line_max_width
        self.items: list[_HelpLabeledListItem] = []
        self.headings: dict[int, str | None] = {}
        self.label_max_length = 0

    def start_block(self, heading: str | None = None):
        self.headings[len(self.items)] = heading

    def add_pair(self, label: str, comment: str):
        if len(label) > self.label_max_length:
            self.label_max_length = len(label)
        self.items.append(_HelpLabeledListItem(label, comment))

    def format_lines(self) -> Iterator[str]:
        label_width = min(self.label_max_length, self.label_max_width)
        text_width = self.line_max_width - label_width - 2
        line_format = '%s{:%d}  {}' % (' ' * HELP_TABLE_INDENT_SIZE, label_width)
        for line_idx, item in enumerate(self.items):
            if line_idx in self.headings:
                heading = self.headings.get(line_idx)
                yield ''
                if heading:
                    yield f'{heading}:'
            if len(item.label) > self.label_max_width:
                yield line_format.format(item.label, '')
                label = ''
            else:
                label = item.label
            text_lines = wrap(item.text.strip(), width=text_width)
            if not text_lines:
                yield line_format.format(label, '')
            else:
                yield line_format.format(label, text_lines[0])
                for text_line in text_lines[1:]:
                    yield line_format.format('', text_line)
        self.label_max_length = 0
        self.items = []

    def format_block(self):
        block_text = os.linesep.join(self.format_lines())
        self.headings = {}
        return block_text


class _HelpBlockFormatter:
    def __init__(self):
        self.chunks: list[str] = []

    def add_blocks(self, *chunks_to_add: str | None):
        for chunk in chunks_to_add:
            chunk = chunk.strip() if chunk else None
            if chunk:
                if self.chunks:
                    self.chunks.append('')
                self.chunks.append(chunk)

    def format_help(self) -> str:
        return os.linesep.join(self.chunks)


class HelpFormatter:
    """Help formatter."""

    def __init__(self,
                 program_name: str,
                 command_names: Sequence[str],
                 description: str,
                 sub_commands_label: str,
                 ):
        """
        Help formatter constructor.

        :param program_name: program name is used for both top level and sub-command help
        :param command_names: command names in appearance order for Usage
        :param description: description for description block
        :param sub_commands_label: label for sub-commands, e.g. 'COMMAND' or 'SUB_COMMAND'
        """
        self.program_name = program_name or '(no name)'
        self.command_names = command_names
        self.description = description
        self.sub_commands_label = sub_commands_label
        self.primary_commands: list[HelpCommandData] = []
        self.secondary_commands: list[HelpCommandData] = []
        self.options: list[HelpOption] = []
        self.arguments: list[HelpArgument] = []
        self.notes: NotesList = []
        self.footnote_builder = FootnoteBuilder()

    def add_command(self,
                    name: str,
                    help_text: str,
                    is_secondary: bool = False,
                    is_hidden: bool = False,
                    has_sub_commands: bool = False,
                    receives_trailing_arguments: bool = False,
                    ):
        """
        Add help information for a sub-command.

        :param name: command name
        :param help_text: help text for command
        :param is_secondary: list in secondary block if True
        :param is_hidden: hide unless option is set to show hidden
        :param has_sub_commands: the command has sub-commands if True
        :param receives_trailing_arguments: receives unparsed trailing arguments if True
        """
        data = HelpCommandData(name,
                               help_text,
                               is_secondary=is_secondary,
                               is_hidden=is_hidden,
                               has_sub_commands=has_sub_commands,
                               receives_trailing_arguments=receives_trailing_arguments)
        if is_secondary:
            self.secondary_commands.append(data)
        else:
            self.primary_commands.append(data)

    def add_option(self,
                   flags: Any,
                   name: str,
                   description: str = None,
                   repeat: Repetition = None,
                   default: DefaultValue = None,
                   choices: Sequence = None,
                   is_boolean: bool = False,
                   ):
        """
        Add help information for a command option.

        :param flags: option flags
        :param name: argument name
        :param description: argument description
        :param repeat: repeat quantity or range as tuple pair
        :param default: default value
        :param choices: restricted value set
        :param is_boolean: handle as a boolean argument or option if True
        """
        self.options.append(
            HelpOption(name,
                       description=description,
                       flags=make_list(flags),
                       repeat=repeat,
                       default=default,
                       choices=choices,
                       is_boolean=is_boolean))

    def add_argument(self,
                     name: str,
                     description: str = None,
                     repeat: Repetition = None,
                     default: DefaultValue = None,
                     choices: Sequence = None,
                     ):
        """
        Add help information for a command argument.

        :param name: argument name
        :param description: argument description
        :param repeat: repeat quantity or range as tuple pair
        :param default: default value
        :param choices: restricted value set
        """
        self.arguments.append(
            HelpArgument(name,
                         description=description,
                         repeat=repeat,
                         default=default,
                         choices=choices))

    def add_note(self, note_text: str):
        """
        Add a note.

        :param note_text: note text to add
        """
        self.notes.append(note_text)

    def add_footnote_dictionary(self, footnotes: NotesDict = None):
        """
        Add a footnotes dictionary.

        :param footnotes: footnotes dictionary
        """
        self.footnote_builder.add_footnotes(footnotes)

    def _format_usage(self,
                      program_name: str,
                      options: list[HelpOption],
                      arguments: list[HelpArgument],
                      command_trailing_arguments: bool,
                      ) -> Iterator[str]:
        parts: list[str] = ['Usage:', program_name]
        parts.extend(self.command_names)
        if options:
            parts.append('[OPTION ...]')
        for argument_idx, argument in enumerate(arguments):
            if command_trailing_arguments and argument_idx == len(arguments) - 1:
                trailing = ' ...'
            else:
                trailing = ''
            repeat = argument.repeat
            if repeat is None:
                if argument.default is None:
                    argument_usage = f'{argument.name}{trailing}'
                else:
                    argument_usage = f'[{argument.name}{trailing}]'
            elif repeat.minimum is not None and repeat.minimum == repeat.maximum:
                argument_usage = ' '.join([argument.name] * repeat.minimum)
            elif repeat.minimum is None or repeat.minimum == 0:
                argument_usage = f'[{argument.name} ...]'
            else:
                argument_usage = f'{argument.name} ...'
            parts.append(argument_usage)
        if self.primary_commands or self.secondary_commands:
            parts.extend([self.sub_commands_label, '...'])
        yield ' '.join(parts)

    def _format_help_text(self, help_text: str) -> str:
        help_text = help_text.strip() if help_text else ''
        start_idx = len(self.footnote_builder.modified_body_paragraphs)
        self.footnote_builder.parse(help_text)
        paragraphs = self.footnote_builder.modified_body_paragraphs[start_idx:]
        output_text = f'{os.linesep}{os.linesep}'.join(paragraphs)
        return output_text

    def _format_description(self) -> Iterator[str]:
        yield self._format_help_text(self.description)

    def _format_table_commands(self,
                               two_column_formatter: _HelpLabeledListFormatter,
                               ) -> Iterator[str]:
        def _add_command(command_data: HelpCommandData):
            if command_data.has_sub_commands:
                name = f'{command_data.name} ...'
            elif command_data.receives_trailing_arguments:
                name = f'{command_data.name} ...'
            else:
                name = command_data.name
            help_text = self._format_help_text(command_data.help_text)
            two_column_formatter.add_pair(name, help_text)
        commands_heading = self.sub_commands_label
        if self.primary_commands:
            two_column_formatter.start_block(heading=commands_heading)
            commands_heading = None
            for command in self.primary_commands:
                _add_command(command)
        if self.secondary_commands:
            two_column_formatter.start_block(heading=commands_heading)
            for command in self.secondary_commands:
                _add_command(command)
        yield two_column_formatter.format_block()

    def _format_table_positionals(self,
                                  two_column_formatter: _HelpLabeledListFormatter,
                                  arguments: list[HelpArgument],
                                  ) -> Iterator[str]:
        if arguments:
            two_column_formatter.start_block(heading='ARGUMENT')
            for argument in arguments:
                description = argument.description
                if description is None:
                    description = '(no argument description)'
                two_column_formatter.add_pair(argument.name,
                                              self._format_help_text(description))
        yield two_column_formatter.format_block()

    def _format_table_options(self,
                              two_column_formatter: _HelpLabeledListFormatter,
                              options: list[HelpOption],
                              ) -> Iterator[str]:
        if options:
            two_column_formatter.start_block(heading='OPTION')
            for option in options:
                description = option.description
                if description is None:
                    description = '(no option description)'
                if option.is_boolean:
                    two_column_formatter.add_pair(
                        f'{"|".join(option.flags)}',
                        self._format_help_text(description))
                else:
                    two_column_formatter.add_pair(
                        f'{"|".join(option.flags)} {option.name}',
                        self._format_help_text(description))
        yield two_column_formatter.format_block()

    def _format_epilog(self, max_width: int) -> str:
        def _format_text(text_block: str | None) -> str:
            if text_block is None:
                return ''
            return os.linesep.join(wrap(text_block, width=max_width))
        if self.notes:
            for note in self.notes:
                yield _format_text(note)
        for footnote_text in self.footnote_builder.format_footnotes():
            yield _format_text(footnote_text)

    @staticmethod
    def _flag_key(flag: str):
        # Option flags are sorted by label text, with the additional logic of
        # equal uppercase letters following lowercase and long options following
        # equal short labels.
        if flag.startswith('-'):
            if flag.startswith('--'):
                group = 'C'
                label = flag[2:]
            else:
                label = flag[1:]
                if label and label[0].isupper():
                    group = 'B'
                    label = label.lower()
                else:
                    group = 'A'
        else:
            # Shouldn't get here.
            group = 'D'
            label = flag
        return ''.join([label, group])

    def format_help(self,
                    receives_trailing_arguments: bool = False,
                    ) -> str:
        # Sort options by (lowercase, original case) tuples so that
        # uppercase always precedes equal but lowercase version. Simply
        # sorting on lowercase keys would not guarantee that result.
        options = list(sorted(self.options, key=lambda a: self._flag_key(a.flags[0])))
        arguments = list(sorted(self.arguments, key=lambda a: a.name))
        terminal_size = get_terminal_size()
        line_max_width = max(HELP_MINIMUM_WRAP_WIDTH,
                             terminal_size.columns - HELP_TABLE_INDENT_SIZE)
        output_formatter = _HelpBlockFormatter()
        output_formatter.add_blocks(
            *self._format_usage(self.program_name,
                                options,
                                self.arguments,
                                receives_trailing_arguments))
        output_formatter.add_blocks(
            *self._format_description())
        two_column_formatter = _HelpLabeledListFormatter(
            HELP_LEFT_COLUMN_MAX_WIDTH, line_max_width)
        output_formatter.add_blocks(
            *self._format_table_commands(two_column_formatter))
        output_formatter.add_blocks(
            *self._format_table_positionals(two_column_formatter, arguments))
        output_formatter.add_blocks(
            *self._format_table_options(two_column_formatter, options))
        output_formatter.add_blocks(
            *self._format_epilog(line_max_width))
        return output_formatter.format_help()


class HelpProvider:
    """Abstract base class for a provider of formatted help text."""

    def format_help(self, *names: str, show_hidden: bool = False) -> str:
        """
        Format help.

        :param names: name parts (name stack)
        :param show_hidden: show hidden help if True
        :return: formatted help text
        """
        raise NotImplementedError
