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

"""Message formatting utilities."""

import os
from typing import Any, Iterator

from .exceptions import format_exception
from .options import OPTIONS


def format_message_lines(text: Any, *args, **kwargs) -> Iterator[str]:
    """Generate message line(s) and indented lines for relevant keyword data.

    Located in the "python" utility library module because of its special
    formatting applied to Python Exception objects.

    Keywords:
    - tag: special prefix string for all lines with an uppercase tag string
    - sub_tag: string to appear in square brackets next to the tag
    - string_file_name: file name to replace '<string>' exception location name

    Args:
        text: primary text
        *args: positional arguments to format as data lines
        **kwargs: keyword arguments to format as data lines

    Returns:
        line iterator
    """
    tag = kwargs.pop('tag', None)
    sub_tag = kwargs.pop('sub_tag', None)
    string_file_name = kwargs.pop('string_file_name', None)

    def _generate_exception_lines(exc: Exception) -> Iterator[str]:
        exc_lines = format_exception(exc).split(os.linesep)
        if exc_lines:
            exc_text = exc_lines[0]
            if string_file_name:
                exc_text = exc_text.replace('<string>', string_file_name)
            yield exc_text
            for exc_line in exc_lines[1:]:
                yield exc_line

    def _generate_raw_lines():
        if text:
            if isinstance(text, (list, tuple)):
                for seq_line in text:
                    yield seq_line
            else:
                yield str(text)
        for value in args:
            if isinstance(value, Exception):
                for exc_value in _generate_exception_lines(value):
                    yield f'{OPTIONS.message_indent}{exc_value}'
            else:
                yield f'{OPTIONS.message_indent}{value}'
        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)):
                for idx, sub_value in enumerate(value):
                    if isinstance(sub_value, Exception):
                        sub_value = format_exception(sub_value)
                    yield f'{OPTIONS.message_indent}{key}[{idx + 1}]: {sub_value}'
            else:
                if isinstance(value, Exception):
                    value = {format_exception(value)}
                yield f'{OPTIONS.message_indent}{key}: {value}'

    if not tag:
        for line in _generate_raw_lines():
            yield line
    else:
        if not sub_tag:
            full_tag = tag.upper()
        else:
            full_tag = f'{tag.upper()}[{sub_tag}]'
        for line in _generate_raw_lines():
            yield f'{full_tag}: {line}'


def format_message_block(message: Any, *args, **kwargs) -> str:
    """Format multi-line message text with positional and keyword arguments.

    Located in the "python" utility library module because of its special
    formatting applied to Python Exception objects.

    "tag" is a special string keyword argument that prefixes all lines with an
    uppercase tag string.

    Args:
        message: primary message text
        *args: positional arguments to format as data lines
        **kwargs: keyword arguments to format as data lines

    Returns:
        formatted multiline message text block
    """
    return os.linesep.join(format_message_lines(message, *args, **kwargs))
