# Copyright (C) 2020-2022, Steven Cooper
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

"""
General-purpose (independent) utilities.

Make sure that any other utility module can import this module without circular
import references. I.e. DO NOT import other utility modules here.

To handle errors independently, avoid functions like console.log_error(), and
either throw an exception or provide an informative return value.
"""

import os
from textwrap import wrap
from typing import Iterable, Any, Text, Iterator, List, Optional, Sequence

from .general import make_list
from .log import abort, display_data
from .options import OPTIONS


def format_table(*rows: Iterable[Any],
                 headers: Iterable[Text] = None,
                 formats: Iterable[Text] = None,
                 display_empty: bool = False,
                 max_width: int = None
                 ) -> Iterator[Text]:
    """
    Generate tabular output from input rows with optional headings.

    :param rows: row data sequences
    :param headers: column header strings
    :param formats: column format strings
    :param display_empty: display headers when there are no rows
    :param max_width: optional maximum full line width used for wrapping the
                      last column as needed
    :return: formatted line generator
    """
    widths: List[int] = []
    format_list = list(formats) if formats is not None else []

    def _get_strings(columns: Iterable[Any], padded: bool = False) -> Iterator[Text]:
        num_columns = 0
        for column_idx, column in enumerate(columns):
            if len(format_list) > column_idx:
                yield column.format(format_list[column_idx])
            else:
                yield str(column)
            num_columns += 1
        if padded:
            for pad_idx in range(len(widths) - num_columns):
                yield ''

    def _check_widths(columns: Iterable[Any]):
        for column_idx, column_string in enumerate(columns):
            column_width = len(column_string)
            if column_idx == len(widths):
                widths.append(column_width)
            elif column_width > widths[column_idx]:
                widths[column_idx] = column_width

    if headers is not None:
        _check_widths(headers)
    row_count = 0
    for row in rows:
        _check_widths(_get_strings(row))
        row_count += 1

    # Calculate wrapping width for last column.
    # Disable wrapping if it doesn't fit well.
    last_width: Optional[int] = None
    if max_width is not None:
        left_columns_width = sum(widths[:-1])
        left_separators_width = len(OPTIONS.column_separator) * (len(widths) - 1)
        last_width = max_width - left_separators_width - left_columns_width
        if last_width < 20:
            last_width = None

    if row_count > 0 or display_empty:

        format_strings = ['{:%d}' % w for w in widths[:-1]]
        format_strings.append('{}')
        format_string = OPTIONS.column_separator.join(format_strings)
        if headers is not None:
            yield format_string.format(*_get_strings(headers, padded=True))
            yield OPTIONS.column_separator.join(['-' * width for width in widths])

        for row in rows:
            if last_width is None:
                yield format_string.format(*_get_strings(row, padded=True))
            else:
                column_strings = list(_get_strings(row, padded=True))
                if len(column_strings[-1]) <= last_width:
                    yield format_string.format(*column_strings)
                else:
                    partial_last_column_lines = wrap(column_strings[-1], width=last_width)
                    for idx, partial_last_column_line in enumerate(partial_last_column_lines):
                        column_strings[-1] = partial_last_column_line
                        yield format_string.format(*column_strings)
                        if idx == 0:
                            column_strings = [''] * len(widths)


def plural(noun: Text, countable: Any):
    """
    Simplistic text pluralization.

    If `countable` length is one:

    - Return unchanged.

    Otherwise if countable length is zero or greater than one:

    - If it ends in 'y', return with ending 'y' replaced by 'ies'.
    - Otherwise return with 's' appended.

    ** No other irregular pluralization cases are handled. Please be aware of
    the input, and how the simplistic algorithm works for it (or not). **

    :param noun: noun to pluralize as needed
    :param countable: item with a length that determines if it is pluralized
    :return: possibly-pluralized noun
    """
    try:
        if len(countable) != 1:
            if noun.endswith('y'):
                return f'{noun[:-1]}ies'
            return f'{noun}s'
    except TypeError:
        pass
    return noun


def fit_text(text: Text,
             width: int,
             placeholder: Text = '...',
             pad: Text = None,
             front: bool = False,
             ):
    """
    Truncate text in various ways.

    Note that this is not word-sensitive, like textwrap.shorten().

    :param text: text to truncate
    :param width: width to truncate to
    :param placeholder: placeholder string (default: '...')
    :param pad: character to use for padding a string shorter than width (default: not padded)
    :param front: truncate from start of string if True
    :return: potentially-truncated or padded text
    """
    placeholder_width = len(placeholder)
    text_width = len(text)
    excess_width = text_width - width
    if excess_width <= 0:
        if pad is None or excess_width == 0:
            return text
        if front:
            return ''.join([pad * (-excess_width), text])
        return ''.join([text, pad * (-excess_width)])
    if front:
        return ''.join([placeholder, text[excess_width + placeholder_width:]])
    else:
        return ''.join([text[:-(excess_width + placeholder_width)], placeholder])


class BlockSplitter:
    def __init__(self, *blocks: str, indent: int = None, double_spaced: bool = False):
        self.lines: List[str] = []
        self.indent = indent
        self.double_spaced = double_spaced
        self.found_indent: Optional[int] = None
        self._trimmed_lines: Optional[List[str]] = None
        for block in blocks:
            self.add_block(block)

    def add_block(self, block: str):
        if self.lines and self.double_spaced:
            self.lines.append('')
        have_empty = False
        have_non_empty = False
        for line in block.split(os.linesep):
            line = line.rstrip()
            line_length = len(line)
            indent = line_length - len(line.lstrip())
            if indent == line_length:
                have_empty = have_non_empty
            else:
                have_non_empty = True
                if have_empty:
                    self.lines.append('')
                    have_empty = False
                self.lines.append(line)
                if self.found_indent is None or indent < self.found_indent:
                    self.found_indent = indent

    @property
    def trimmed_lines(self) -> List[str]:
        indent = ' ' * self.indent if self.indent else ''
        if self._trimmed_lines is None:
            if self.found_indent:
                self._trimmed_lines = [indent + line[self.found_indent:] for line in self.lines]
            else:
                self._trimmed_lines = [indent + line for line in self.lines]
        return self._trimmed_lines


def trim_text_blocks(*blocks: str,
                     indent: int = None,
                     keep_indent: bool = False,
                     double_spaced: bool = False,
                     ) -> List[str]:
    splitter = BlockSplitter(*blocks, indent=indent, double_spaced=double_spaced)
    if keep_indent:
        return splitter.lines
    return splitter.trimmed_lines


def trim_text_block(block: str,
                    indent: int = None,
                    keep_indent: bool = False,
                    double_spaced: bool = False,
                    ) -> str:
    return os.linesep.join(trim_text_blocks(block,
                                            indent=indent,
                                            keep_indent=keep_indent,
                                            double_spaced=double_spaced))


class StringExpansionError(RuntimeError):
    """String expansion exception."""

    def __init__(self, value: str, *missing_symbols: str):
        """
        Constructor.

        :param value: value that failed expansion
        :param missing_symbols: missing symbols
        """
        self.missing_symbols = missing_symbols
        unresolved = self.wrapped_symbol_string
        super().__init__(f'String expansion error: {value=} {unresolved=}')

    @property
    def wrapped_symbol_string(self) -> str:
        """
        Provide {}-wrapped symbol string for error display.

        :return: wrapped symbol string
        """
        return ' '.join([f'{{{symbol}}}' for symbol in self.missing_symbols])


def expand_value(value: Any, symbols: dict) -> str:
    """
    Produce an expanded string for a value and symbols.

    :param value: value to expand
    :param symbols: substitution symbols
    :return: expanded string
    :raise StringExpansionError: if symbols are missing, etc.
    """
    if isinstance(value, (tuple, list)):
        return ' '.join([expand_value(element, symbols) for element in value])
    if not isinstance(value, str):
        return str(value)
    output_string: Optional[str] = None
    bad_names: list[str] = []
    # The loop allows all unresolved symbols to be discovered.
    while output_string is None:
        try:
            output_string = value.format(**symbols)
            if bad_names:
                if OPTIONS.is_debug():
                    display_data(symbols, heading='symbols')
                raise StringExpansionError(value, *bad_names)
        except AttributeError as attr_exc:
            display_data(value, heading='expansion string')
            abort(f'Bad string expansion attribute (see exception below).', attr_exc)
        except KeyError as key_exc:
            # Strip out surrounding single quotes from exception text to get key name.
            name = str(key_exc)[1:-1]
            if not bad_names:
                symbols = symbols.copy()
            symbols[name] = '???'
            bad_names.append(name)
    return output_string


def format_block_lines(*blocks: str | Sequence,
                       indent: int = None,
                       double_spaced: bool = False,
                       keep_indent: bool = False,
                       ) -> list[str]:
    """
    Reformat text blocks as line strings.

    :param blocks: blocks to reformat
    :param indent: optional number of spaces to insert for each line
    :param double_spaced: add blank line between blocks if True
    :param keep_indent: preserve current indentation if True
    :return: reformatted lines (not blocks)
    """
    lines: list[str] = []
    minimum_leading_spaces: Optional[int] = None
    for block_text_or_sequence in blocks:
        if lines and double_spaced:
            lines.append('')
        for block in make_list(block_text_or_sequence):
            have_empty = False
            have_non_empty = False
            for line in block.split(os.linesep):
                line = line.rstrip()
                line_length = len(line)
                leading_spaces = line_length - len(line.lstrip())
                if leading_spaces == line_length:
                    have_empty = have_non_empty
                else:
                    have_non_empty = True
                    if have_empty:
                        lines.append('')
                        have_empty = False
                    lines.append(line)
                    if minimum_leading_spaces is None or leading_spaces < minimum_leading_spaces:
                        minimum_leading_spaces = leading_spaces
    indent_string = ' ' * indent if indent else ''
    if keep_indent:
        return lines
    if minimum_leading_spaces:
        return [indent_string + line[minimum_leading_spaces:] for line in lines]
    return [indent_string + line for line in lines]


def format_block_text(*blocks: str | Sequence,
                      indent: int = None,
                      double_spaced: bool = False,
                      keep_indent: bool = False,
                      ) -> str:
    """
    Reformat text blocks as a single string.

    :param blocks: blocks to reformat
    :param indent: optional number of spaces to insert for each line
    :param double_spaced: add blank line between blocks if True
    :param keep_indent: preserve current indentation if True
    :return: reformatted text string
    """
    lines = format_block_lines(*blocks,
                               indent=indent,
                               double_spaced=double_spaced,
                               keep_indent=keep_indent)
    return os.linesep.join(lines)
