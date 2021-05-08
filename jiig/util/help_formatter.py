"""Custom help formatting."""

import os
from dataclasses import dataclass
from shutil import get_terminal_size
from textwrap import wrap
from typing import Text, List, Optional, Iterator, Dict, Sequence

from .footnotes import FootnoteBuilder, NotesList, NotesDict
from .general import DefaultValue
from .repetition import Repetition


class Footnote:
    def __init__(self, text: Text):
        self.text = text.strip()
        self.option_flags: List[Text] = []
        self.argument_dests: List[Text] = []


@dataclass
class HelpCommandData:
    name: Text
    help_text: Text
    is_secondary: bool = False
    is_hidden: bool = False
    has_sub_commands: bool = False
    receives_trailing_arguments: bool = False


@dataclass
class HelpOption:
    name: Text
    description: Text = None
    flags: List[Text] = None
    repeat: Repetition = None
    default: DefaultValue = None
    choices: Sequence = None
    is_boolean: bool = False

    def __post_init__(self):
        self.name = self.name.upper()


@dataclass
class HelpArgument:
    name: Text
    description: Text = None
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
    label: Text
    text: Text


class _HelpLabeledListFormatter:

    labeled_list_separator = '  '

    def __init__(self,
                 label_max_width: int,
                 line_max_width: int,
                 ):
        self.label_max_width = label_max_width
        self.line_max_width = line_max_width
        self.items: List[_HelpLabeledListItem] = []
        self.headings: Dict[int, Optional[Text]] = {}
        self.label_max_length = 0

    def start_block(self, heading: Optional[Text] = None):
        self.headings[len(self.items)] = heading

    def add_pair(self, label: Text, comment: Text):
        if len(label) > self.label_max_length:
            self.label_max_length = len(label)
        self.items.append(_HelpLabeledListItem(label, comment))

    def format_lines(self) -> Iterator[Text]:
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
                yield label
            else:
                yield line_format.format(label, text_lines[0])
                for text_line in text_lines[1:]:
                    yield line_format.format('', text_line)
        self.label_max_length = 0
        self.items = []

    def format_block(self):
        return os.linesep.join(self.format_lines())


class _HelpBlockFormatter:
    def __init__(self):
        self.chunks: List[Text] = []

    def add_blocks(self, *chunks_to_add: Optional[Text]):
        for chunk in chunks_to_add:
            chunk = chunk.strip() if chunk else None
            if chunk:
                if self.chunks:
                    self.chunks.append('')
                self.chunks.append(chunk)

    def format_help(self) -> Text:
        return os.linesep.join(self.chunks)


class HelpFormatter:

    def __init__(self,
                 program_name: Text,
                 command_names: Sequence[Text],
                 description: Text,
                 sub_commands_label: Text,
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
        self.description = description or '(no description)'
        self.sub_commands_label = sub_commands_label
        self.commands: List[HelpCommandData] = []
        self.options: List[HelpOption] = []
        self.arguments: List[HelpArgument] = []
        self.notes: NotesList = []
        self.footnote_builder = FootnoteBuilder()

    def add_command(self,
                    name: Text,
                    help_text: Text,
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
        self.commands.append(
            HelpCommandData(name,
                            help_text,
                            is_secondary=is_secondary,
                            is_hidden=is_hidden,
                            has_sub_commands=has_sub_commands,
                            receives_trailing_arguments=receives_trailing_arguments))

    def add_option(self,
                   flags: List[Text],
                   name: Text,
                   description: Text = None,
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
                       flags=flags,
                       repeat=repeat,
                       default=default,
                       choices=choices,
                       is_boolean=is_boolean))

    def add_argument(self,
                     name: Text,
                     description: Text = None,
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

    def add_note(self, note_text: Text):
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
                      program_name: Text,
                      options: List[HelpOption],
                      arguments: List[HelpArgument],
                      command_trailing_arguments: bool,
                      ) -> Iterator[Text]:
        parts: List[Text] = ['Usage:', program_name]
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
        if self.commands:
            parts.extend([self.sub_commands_label, '...'])
        yield ' '.join(parts)

    def _format_help_text(self, help_text: Optional[Text]) -> Text:
        help_text = help_text.strip() if help_text else ''
        if not help_text:
            return '(no help available)'
        return self.footnote_builder.scan_text(help_text)

    def _format_description(self) -> Iterator[Text]:
        yield self._format_help_text(self.description)

    def _format_table_commands(self,
                               two_column_formatter: _HelpLabeledListFormatter,
                               show_hidden: bool = False,
                               ) -> Iterator[Text]:
        def _add_command(command_data: HelpCommandData):
            if show_hidden or not command_data.is_hidden:
                if command_data.has_sub_commands:
                    name = f'{command_data.name} ...'
                elif command_data.receives_trailing_arguments:
                    name = f'{command_data.name} ...'
                else:
                    name = command_data.name
                two_column_formatter.add_pair(
                    name, self._format_help_text(command_data.help_text))
        if self.commands:
            two_column_formatter.start_block(heading=self.sub_commands_label)
            primary_commands = filter(
                lambda st: not st.is_secondary,
                self.commands)
            for command in primary_commands:
                _add_command(command)
            secondary_commands = filter(
                lambda st: st.is_secondary,
                self.commands)
            if secondary_commands:
                two_column_formatter.start_block()
                for command in secondary_commands:
                    _add_command(command)
        yield two_column_formatter.format_block()

    def _format_table_positionals(self,
                                  two_column_formatter: _HelpLabeledListFormatter,
                                  arguments: List[HelpArgument],
                                  ) -> Iterator[Text]:
        if arguments:
            two_column_formatter.start_block(heading='ARGUMENT')
            for argument in arguments:
                two_column_formatter.add_pair(
                    argument.name, self._format_help_text(argument.description))
        yield two_column_formatter.format_block()

    def _format_table_options(self,
                              two_column_formatter: _HelpLabeledListFormatter,
                              options: List[HelpOption],
                              ) -> Iterator[Text]:
        if options:
            two_column_formatter.start_block(heading='OPTION')
            for option in options:
                if option.is_boolean:
                    two_column_formatter.add_pair(
                        f'{"|".join(option.flags)}',
                        self._format_help_text(option.description))
                else:
                    two_column_formatter.add_pair(
                        f'{"|".join(option.flags)} {option.name}',
                        self._format_help_text(option.description))
        yield two_column_formatter.format_block()

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

    def format_help(self,
                    show_hidden: bool = False,
                    receives_trailing_arguments: bool = False,
                    ) -> Text:
        # Sort options by (lowercase, original case) tuples so that
        # uppercase always precedes equal but lowercase version. Simply
        # sorting on lowercase keys would not guarantee that result.
        options = list(sorted(self.options, key=lambda a: (a.flags[0].lower(), a.flags[0])))
        arguments = list(sorted(self.arguments, key=lambda a: a.name))
        terminal_size = get_terminal_size()
        line_max_width = max(HELP_MINIMUM_WRAP_WIDTH,
                             terminal_size.columns - HELP_TABLE_INDENT_SIZE)
        output_formatter = _HelpBlockFormatter()
        output_formatter.add_blocks(
            *self._format_usage(self.program_name,
                                options,
                                arguments,
                                receives_trailing_arguments))
        output_formatter.add_blocks(
            *self._format_description())
        two_column_formatter = _HelpLabeledListFormatter(
            HELP_LEFT_COLUMN_MAX_WIDTH, line_max_width)
        output_formatter.add_blocks(
            *self._format_table_commands(two_column_formatter, show_hidden=show_hidden))
        output_formatter.add_blocks(
            *self._format_table_positionals(two_column_formatter, arguments))
        output_formatter.add_blocks(
            *self._format_table_options(two_column_formatter, options))
        output_formatter.add_blocks(
            *self._format_epilog(line_max_width))
        return output_formatter.format_help()


class HelpProvider:
    """Abstract base class for a provider of formatted help text."""

    def format_help(self, *names: Text, show_hidden: bool = False) -> Text:
        """
        Format help.

        :param names: name parts (name stack)
        :param show_hidden: show hidden help if True
        :return: formatted help text
        """
        raise NotImplementedError
