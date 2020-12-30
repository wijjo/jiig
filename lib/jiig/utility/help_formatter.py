"""Custom help formatting."""

import os
from dataclasses import dataclass
from shutil import get_terminal_size
from textwrap import wrap
from typing import Text, List, Tuple, Optional, Iterator, Dict, Any, Sequence, Union

from .footnotes import FootnoteBuilder, NotesList, NotesDict
from .general import format_table


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


@dataclass
class HelpOption:
    name: Text
    description: Text = None
    cardinality: Union[Text, int] = None
    flags: List[Text] = None
    default_value: Any = None
    choices: Sequence = None
    is_boolean: bool = False


@dataclass
class HelpArgument:
    name: Text
    description: Text = None
    cardinality: Union[Text, int] = None
    default_value: Any = None
    choices: Sequence = None


HELP_TABLE_INDENT_SIZE = 2
HELP_MINIMUM_WRAP_WIDTH = 40


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
                    ):
        """
        Add help information for a sub-command.

        :param name: command name
        :param help_text: help text for command
        :param is_secondary: list in secondary block if True
        :param is_hidden: hide unless option is set to show hidden
        :param has_sub_commands: the command has sub-commands if True
        """
        self.commands.append(
            HelpCommandData(name,
                            help_text,
                            is_secondary=is_secondary,
                            is_hidden=is_hidden,
                            has_sub_commands=has_sub_commands))

    def add_option(self,
                   flags: List[Text],
                   name: Text,
                   description: Text = None,
                   cardinality: Union[Text, int] = None,
                   default_value: Any = None,
                   choices: Sequence = None,
                   is_boolean: bool = False,
                   ):
        """
        Add help information for a command option.

        :param flags: option flags
        :param name: argument name
        :param description: argument description
        :param cardinality: quantity or cardinality flag
        :param default_value: default value
        :param choices: restricted value set
        :param is_boolean: handle as a boolean argument or option if True
        """
        self.options.append(
            HelpOption(name,
                       description=description,
                       cardinality=cardinality,
                       flags=flags,
                       default_value=default_value,
                       choices=choices,
                       is_boolean=is_boolean))

    def add_argument(self,
                     name: Text,
                     description: Text = None,
                     cardinality: Union[Text, int] = None,
                     default_value: Any = None,
                     choices: Sequence = None,
                     ):
        """
        Add help information for a command argument.

        :param name: argument name
        :param description: argument description
        :param cardinality: quantity or cardinality flag
        :param default_value: default value
        :param choices: restricted value set
        """
        self.arguments.append(
            HelpArgument(name,
                         description=description,
                         cardinality=cardinality,
                         default_value=default_value,
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

    def _format_usage(self,
                      program_name: Text,
                      options: List[HelpOption],
                      arguments: List[HelpArgument],
                      ) -> Iterator[Text]:
        parts: List[Text] = ['Usage:', program_name]
        parts.extend(self.command_names)
        if options:
            parts.append('[OPTION ...]')
        for argument in arguments:
            if not argument.cardinality or argument.cardinality == '?':
                parts.append(f'[{argument.name}]')
            elif argument.cardinality == 1 or argument.cardinality == '1':
                parts.append(argument.name)
            elif argument.cardinality == '*':
                parts.append(f'[{argument.name} ...]')
            else:
                parts.append(f'{argument.name} [{argument.name} ...]')
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

    def _add_table_commands(self, table_builder: TableFormatter, show_hidden: bool = False):
        def _add_command(command_data: HelpCommandData):
            if show_hidden or not command_data.is_hidden:
                name = f'{command_data.name} ...' if command_data.has_sub_commands else command_data.name
                table_builder.add_row(name, self._format_help_text(command_data.help_text))
        if self.commands:
            table_builder.start_block(heading=self.sub_commands_label)
            primary_commands = filter(
                lambda st: not st.is_secondary,
                self.commands)
            for command in primary_commands:
                _add_command(command)
            secondary_commands = filter(
                lambda st: st.is_secondary,
                self.commands)
            if secondary_commands:
                table_builder.start_block()
                for command in secondary_commands:
                    _add_command(command)

    def _add_table_positionals(self,
                               table_builder: TableFormatter,
                               arguments: List[HelpArgument],
                               ):
        if arguments:
            table_builder.start_block(heading='ARGUMENT')
            for argument in arguments:
                table_builder.add_row(argument.name,
                                      self._format_help_text(argument.description))

    def _add_table_options(self,
                           table_builder: TableFormatter,
                           options: List[HelpOption],
                           ):
        if options:
            table_builder.start_block(heading='OPTION')
            for option in options:
                if option.is_boolean:
                    table_builder.add_row(f'{"|".join(option.flags)}',
                                          self._format_help_text(option.description))
                else:
                    table_builder.add_row(f'{"|".join(option.flags)} {option.name}',
                                          self._format_help_text(option.description))

    def _format_tables(self,
                       options: List[HelpOption],
                       arguments: List[HelpArgument],
                       width: int,
                       show_hidden: bool = False,
                       ) -> Iterator[Text]:
        table_builder = self.TableFormatter(width)
        self._add_table_commands(table_builder, show_hidden=show_hidden)
        self._add_table_positionals(table_builder, arguments)
        self._add_table_options(table_builder, options)
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
        # Sort options by (lowercase, original case) tuples so that
        # uppercase always precedes equal but lowercase version. Simply
        # sorting on lowercase keys would not guarantee that result.
        options = list(sorted(self.options, key=lambda a: (a.flags[0].lower(), a.flags[0])))
        arguments = list(sorted(self.arguments, key=lambda a: a.name))
        terminal_size = get_terminal_size()
        max_width = max(HELP_MINIMUM_WRAP_WIDTH,
                        terminal_size.columns - HELP_TABLE_INDENT_SIZE)
        builder = self.OutputFormatter()
        builder.add_block(*self._format_usage(self.program_name, options, arguments))
        builder.add_block(*self._format_description())
        builder.add_block(*self._format_tables(options,
                                               arguments,
                                               max_width,
                                               show_hidden=show_hidden))
        builder.add_block(*self._format_epilog(max_width))
        return builder.format_help()


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
