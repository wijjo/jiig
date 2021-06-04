"""
Context for text expansion and external command execution environment.
"""

import os
import sys
from contextlib import contextmanager
from pprint import pformat
from typing import List, Union, ContextManager, Optional, Any, TypeVar, Type

from .console import log_heading, log_warning, log_error, log_message, abort
from .general import trim_text_blocks
from .options import Options

T_context = TypeVar('T_context', bound='Context')


class Context:
    """Nestable execution context with text expansion symbols."""

    def __init__(self):
        """Construct context."""
        # Give useful symbols for free, e.g. newline.
        self.symbols = {'nl': os.linesep}

    def update(self, **kwargs):
        """
        Update context symbols with text expansion.

        Expands in original caller's keyword argument order, which allows
        dependencies to resolve within this one operation. (see PEP-468)

        :param kwargs: keyword symbols to expand and copy
        """
        try:
            for key, value in kwargs.items():
                self.symbols[key] = self.format(value)
        except ValueError as exc:
            self.abort(str(exc))

    def copy_symbols(self, **kwargs):
        """
        Copy symbols to context without text expansion.

        :param kwargs: keyword symbols to copy
        """
        self.symbols.update(kwargs)

    @contextmanager
    def sub_context(self, **kwargs) -> ContextManager[T_context]:
        """
        Create sub-context with a contextmanager wrapper.

        :param kwargs: keyword symbols for expansion
        :return: child context
        """
        original_working_folder = os.getcwd()
        child_context = self.create_child_context(**kwargs)
        yield child_context
        # Restore working folder, but only if changed using Context.chdir().
        if child_context.working_folder_changed:
            os.chdir(original_working_folder)

    @contextmanager
    def custom_context(self,
                       context_class: Type[T_context],
                       **kwargs,
                       ) -> ContextManager[T_context]:
        """
        Create custom sub-context with a contextmanager wrapper.

        :param context_class: custom context class
        :param kwargs: additional keyword symbols for expansion
        :return: child context
        """
        with context_class().sub_context(**kwargs) as sub_context:
            original_working_folder = os.getcwd()
            sub_context.copy_symbols(**self.symbols)
            yield sub_context
            if sub_context.working_folder_changed:
                os.chdir(original_working_folder)

    def clone(self) -> T_context:
        """
        Overridable method to clone a context.

        Subclasses with extended constructors and or extra data members should
        override this method to properly initialize a new instance.

        :return: cloned context instance
        """
        return self.__class__()

    def create_child_context(self, **kwargs) -> T_context:
        """
        Create child context without a contextmanager wrapper.

        :param kwargs: keyword symbols for expansion
        :return: child context
        """
        child_context = self.clone()
        child_context.copy_symbols(**self.symbols)
        child_context.update(**kwargs)
        return child_context

    def format(self, text: Optional[Union[str, list, tuple]]) -> Optional[Union[str, List[str]]]:
        """
        Format text with context symbol expansion.

        :param text: text to format
        :return: formatted text or None if text was None
        """
        if text is None:
            return None
        if isinstance(text, (list, tuple)):
            return [str(item).format(**self.symbols) for item in text]
        try:
            return str(text).format(**self.symbols)
        except KeyError as key_error:
            if Options.debug:
                sys.stderr.write(
                    os.linesep.join([
                        '====== text for expansion ======',
                        text,
                        '====== symbols for expansion ======',
                        pformat(self.symbols, indent=2),
                        '======',
                        '',
                    ])
                )
            self.abort(f'Bad expansion key {str(key_error)}.', text)

    def format_path(self, path: str) -> str:
        """
        Calls format() after fixing slashes, as needed.

        :param path: input path to expand
        :return: expanded path string
        """
        if os.path.sep != '/':
            path = path.replace('/', os.path.sep)
        return self.format(path)

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

    def get(self, name, default: Any = None) -> Optional[Any]:
        """
        Get a symbol's value.

        :param name: symbol name
        :param default: optional default value (default: None)
        :return: value or None if name not found
        """
        return self.symbols.get(name, default)

    def has(self, name) -> bool:
        """
        Check if a symbol is present.

        :param name: symbol name
        :return: True if the symbol exists
        """
        return name in self.symbols

    def message(self, message: Optional[str], *args, **kwargs):
        """
        Display console message with symbol expansion.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        log_message(self.format(message), *args, **kwargs)

    def warning(self, message: Optional[str], *args, **kwargs):
        """
        Display console warning message with symbol expansion.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        log_warning(self.format(message), *args, **kwargs)

    def error(self, message: Optional[str], *args, **kwargs):
        """
        Display console error message with symbol expansion.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        log_error(self.format(message), *args, **kwargs)

    def abort(self, message: Optional[str], *args, **kwargs):
        """
        Display console fatal error message with symbol expansion and abort execution.

        :param message: message to expand and display
        :param args: positional arguments to display below message
        :param kwargs: keyword arguments to display with names below message
        """
        lines = [self.format(message)]
        if not Options.debug:
            lines.append('(use debug option for more details)')
        abort(*lines, *args, **kwargs)

    def heading(self, level: int, message: Optional[str]):
        """
        Display console heading message with symbol expansion.

        :param level: heading level, 1-n
        :param message: message to expand and display
        """
        log_heading(level, self.format(message))

    def format_quoted(self, text: str) -> str:
        """
        Expands symbols, wraps in double quotes as needed, and escapes embedded quotes.

        :param text: text to expand, escape, and quote
        :return: quoted expanded text
        """
        expanded = self.format(text)
        if not set(expanded).intersection((' ', '"')):
            return expanded
        escaped = expanded.replace('"', '\\"')
        return f'"{escaped}"'
