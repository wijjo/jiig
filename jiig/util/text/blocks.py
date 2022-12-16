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
Text block formatting.
"""

import os
from typing import Sequence


def fit_text(text: str,
             width: int,
             placeholder: str = '...',
             pad: str = None,
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
        self.lines: list[str] = []
        self.indent = indent
        self.double_spaced = double_spaced
        self.found_indent: int | None = None
        self._trimmed_lines: list[str] | None = None
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
    def trimmed_lines(self) -> list[str]:
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
                     ) -> list[str]:
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
    minimum_leading_spaces: int | None = None
    for block_item in blocks:
        if not block_item:
            lines.append('')
            continue
        if lines and double_spaced:
            lines.append('')
        block_list = block_item if isinstance(block_item, (list, tuple)) else [block_item]
        for block in block_list:
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
