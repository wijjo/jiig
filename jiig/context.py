# Copyright (C) 2021-2023, Steven Cooper
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

"""Context for text expansion accessed by command implementations."""

import os
import sys
from pathlib import Path
from pprint import pformat
from typing import Any, Self

from .util.collections import AttributeDictionary
from .util.log import log_heading, log_warning, log_error, log_message, abort
from .util.options import OPTIONS
from .util.text.blocks import trim_text_blocks


class Context:
    """Nestable execution context with text expansion symbols.

    Public data members:
    - s: Dictionary and attribute style access to expansion symbols.
    """

    def __init__(self, parent: Self | None, **kwargs):
        """Construct context, possibly inheriting from a parent context.

        Args:
            parent: optional parent context
            **kwargs: initial symbols
        """
        if parent is not None:
            self.s = AttributeDictionary.new(no_defaults=True)
            self.copy_symbols(**parent.s)
        else:
            self.s = AttributeDictionary.new(no_defaults=True)
        self.update(**kwargs)
        # Give useful symbols for free, e.g. newline.
        if 'nl' not in self.s:
            self.s['nl'] = os.linesep
        self.on_initialize()

    def context(self, **kwargs) -> Self:
        """Create a sub-context.

        Args:
            **kwargs: sub-context symbols

        Returns:
            sub-context
        """
        return self.__class__(self, **kwargs)

    def on_initialize(self):
        """Sub-class initialization call-back.

        Allows some sub-classes to avoid overriding the constructor.
        """
        pass

    def __enter__(self) -> Self:
        """Context management protocol enter method.

        Called at the start when used in a with block. Implemented only for
        consistency with sub-classes that have actual state to save and restore.

        Returns:
            Context object
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context management protocol exit method.

        Args:
            exc_type: exception type
            exc_val: exception value
            exc_tb: exception traceback

        Returns:
            True to suppress an exception that occurred in the with block
        """
        return False

    def update(self, **kwargs) -> Self:
        """Update context symbols with text expansion.

        Expands in original caller's keyword argument order, which allows
        dependencies to resolve within this one operation. (see PEP-468)

        This is chainable to allow use in the same `with` statement that creates
        the context.

        Args:
            **kwargs: keyword symbols to expand and copy
        """
        try:
            for key, value in kwargs.items():
                self.s[key] = self.format(value)
            return self
        except ValueError as exc:
            self.abort(str(exc))

    def copy_symbols(self, **kwargs) -> Self:
        """Copy symbols to context without text expansion.

        This is chainable to allow use in the same `with` statement that creates
        the context.

        Args:
            **kwargs: keyword symbols to copy
        """
        self.s.update(kwargs)
        return self

    def format(self, text: str | list | tuple | None) -> str | list[str] | None:
        """Format text with context symbol expansion.

        Args:
            text: text to format

        Returns:
            formatted text or None if text was None
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
        """Calls format() after joining path parts and fixing slashes, as needed.

        Args:
            path: top level path to expand
            *sub_paths: sub-paths to expand

        Returns:
            expanded path string
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
        """Format text blocks.

        Expand symbols, trim excess indentation and outer whitespace, optionally
        add indentation, and optionally double-space lines.

        Args:
            *blocks: text blocks to format
            indent: optional indentation amount
            double_spaced: add extra line separators between blocks if true

        Returns:
            formatted text
        """
        lines = trim_text_blocks(*blocks, indent=indent, double_spaced=double_spaced)
        return os.linesep.join([self.format(line) for line in lines])

    def message(self, message: Any, *args, **kwargs):
        """Display console message with symbol expansion.

        Args:
            message: message to expand and display
            *args: positional arguments to display below message
            **kwargs: keyword arguments to display with names below message
        """
        log_message(self.format(message), *args, **kwargs)

    def warning(self, message: Any, *args, **kwargs):
        """Display console warning message with symbol expansion.

        Args:
            message: message to expand and display
            *args: positional arguments to display below message
            **kwargs: keyword arguments to display with names below message
        """
        log_warning(self.format(message), *args, **kwargs)

    def error(self, message: Any, *args, **kwargs):
        """Display console error message with symbol expansion.

        Args:
            message: message to expand and display
            *args: positional arguments to display below message
            **kwargs: keyword arguments to display with names below message
        """
        log_error(self.format(message), *args, **kwargs)

    def abort(self, message: Any, *args, **kwargs):
        """Display console fatal error message with symbol expansion and abort execution.

        Args:
            message: message to expand and display
            *args: positional arguments to display below message
            **kwargs: keyword arguments to display with names below message
        """
        lines = [self.format(message)]
        if not OPTIONS.debug:
            lines.append('(use debug option for more details)')
        abort(*lines, *args, **kwargs)

    def heading(self, level: int, message: Any):
        """Display console heading message with symbol expansion.

        Args:
            level: heading level, 1-n
            message: message to expand and display
        """
        log_heading(self.format(message), level=level)


class ActionContext(Context):
    """Nestable execution context with text expansion symbols.

    Supports temporary working folder location changes.

    Supports text expansion capabilities provided by base Context class.
    """

    def __init__(self, parent: Context | None, **kwargs):
        """Construct action context.

        Args:
            parent: optional parent context for symbol inheritance
            **kwargs: initial symbols
        """
        super().__init__(parent, **kwargs)
        self.initial_working_folder = Path(os.getcwd())
        self.working_folder_changed = False
        # Convenient access to Jiig runtime options.
        self.options = OPTIONS

    def __enter__(self) -> Self:
        """Context management protocol enter method.

        Called at the start when an ActionContext is used in a with block. Saves
        the working directory.

        Returns:
            Context object
        """
        self.initial_working_folder = Path(os.getcwd())
        self.working_folder_changed = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context management protocol exit method.

        Called at the end when an ActionContext is used in a with block.
        Restores the original working directory if it was changed by calling
        working_folder() method.

        Args:
            exc_type: exception type
            exc_val: exception value
            exc_tb: exception traceback

        Returns:
            True to suppress an exception that occurred in the with block
        """
        if self.working_folder_changed:
            os.chdir(self.initial_working_folder)
            self.working_folder_changed = False
        return False

    def working_folder(self, folder: str | Path) -> Path:
        """Change the working folder.

        Original working folder is restored by the contextmanager wrapped around
        the sub_context creation.

        Args:
            folder: new working folder

        Returns:
            previous working folder as pathlib.Path
        """
        os.chdir(folder)
        self.working_folder_changed = True
        return Path(os.getcwd())
