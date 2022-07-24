# Copyright (C) 2021-2022, Steven Cooper
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
Context for text expansion and external command execution environment.
"""

import os
import sys
from pprint import pformat
from typing import List, Union, Optional, Any

from ..util import OPTIONS
from ..util.log import log_heading, log_warning, log_error, log_message, abort
from ..util.general import trim_text_blocks, AttrDictNoDefaults


class Context:
    """
    Nestable execution context with text expansion symbols.

    Public data members:
    - s: Dictionary and attribute style access to expansion symbols.
    """

    def __init__(self, parent: Optional['Context'], **kwargs):
        """
        Construct context, possibly inheriting from a parent context.

        :param parent: optional parent context
        :param kwargs: initial symbols
        """
        if parent is not None:
            self.s = AttrDictNoDefaults()
            self.copy_symbols(**parent.s)
            self.update(**kwargs)
        else:
            self.s = AttrDictNoDefaults(kwargs)
        # Give useful symbols for free, e.g. newline.
        if 'nl' not in self.s:
            self.s['nl'] = os.linesep
        self.on_initialize()

    def context(self, **kwargs) -> 'Context':
        """
        Create a sub-context.

        :param kwargs: sub-context symbols
        :return: sub-context
        """
        return self.__class__(self, **kwargs)

    def on_initialize(self):
        """
        Sub-class initialization call-back.

        Allows some sub-classes to avoid overriding the constructor.
        """
        pass

    def __enter__(self) -> 'Context':
        """
        Context management protocol enter method.

        Called at the start when used in a with block. Implemented only for
        consistency with sub-classes that have actual state to save and restore.

        :return: Context object
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context management protocol exit method.

        :param exc_type: exception type
        :param exc_val: exception value
        :param exc_tb: exception traceback
        :return: True to suppress an exception that occurred in the with block
        """
        return False

    def update(self, **kwargs) -> 'Context':
        """
        Update context symbols with text expansion.

        Expands in original caller's keyword argument order, which allows
        dependencies to resolve within this one operation. (see PEP-468)

        This is chainable to allow use in the same `with` statement that creates
        the context.

        :param kwargs: keyword symbols to expand and copy
        """
        try:
            for key, value in kwargs.items():
                self.s[key] = self.format(value)
            return self
        except ValueError as exc:
            self.abort(str(exc))

    def copy_symbols(self, **kwargs) -> 'Context':
        """
        Copy symbols to context without text expansion.

        This is chainable to allow use in the same `with` statement that creates
        the context.

        :param kwargs: keyword symbols to copy
        """
        self.s.update(kwargs)
        return self

    def format(self, text: Optional[Union[str, list, tuple]]) -> Optional[Union[str, List[str]]]:
        """
        Format text with context symbol expansion.

        :param text: text to format
        :return: formatted text or None if text was None
        """
        if text is None:
            return None
        if isinstance(text, (list, tuple)):
            return [str(item).format(**self.s) for item in text]
        try:
            return str(text).format(**self.s)
        except KeyError as key_error:
            if OPTIONS.debug:
                sys.stderr.write(
                    os.linesep.join([
                        '====== text for expansion ======',
                        text,
                        '====== symbols for expansion ======',
                        pformat(self.s, indent=2),
                        '======',
                        '',
                    ])
                )
            self.abort(f'Bad expansion key {str(key_error)}.', text)

    def format_path(self, path: str, *sub_paths: str) -> str:
        """
        Calls format() after joining path parts and fixing slashes, as needed.

        :param path: top level path to expand
        :param sub_paths: sub-paths to expand
        :return: expanded path string
        """
        full_path = os.path.join(path, *sub_paths) if sub_paths else path
        if os.path.sep != '/':
            full_path = full_path.replace('/', os.path.sep)
        return self.format(full_path)

    def format_blocks(self,
                      *blocks: str,
                      indent: int = None,
                      double_spaced: bool = False,
                      ) -> str:
        """
        Format text blocks.

        Expand symbols, trim excess indentation and outer whitespace, optionally
        add indentation, and optionally double-space lines.

        :param blocks: text blocks to format
        :param indent: optional indentation amount
        :param double_spaced: add extra line separators between blocks if true
        :return: formatted text
        """
        lines = trim_text_blocks(*blocks, indent=indent, double_spaced=double_spaced)
        return os.linesep.join([self.format(line) for line in lines])

    def message(self, message: Any, *args, **kwargs):
        """
        Display console message with symbol expansion.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        log_message(self.format(message), *args, **kwargs)

    def warning(self, message: Any, *args, **kwargs):
        """
        Display console warning message with symbol expansion.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        log_warning(self.format(message), *args, **kwargs)

    def error(self, message: Any, *args, **kwargs):
        """
        Display console error message with symbol expansion.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        log_error(self.format(message), *args, **kwargs)

    def abort(self, message: Any, *args, **kwargs):
        """
        Display console fatal error message with symbol expansion and abort execution.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        lines = [self.format(message)]
        if not OPTIONS.debug:
            lines.append('(use debug option for more details)')
        abort(*lines, *args, **kwargs)

    def heading(self, level: int, message: Any):
        """
        Display console heading message with symbol expansion.

        :param level: heading level, 1-n
        :param message: message to expand and display
        """
        log_heading(level, self.format(message))
