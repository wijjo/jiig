"""
Scripter context.
"""

import os
import sys
from contextlib import contextmanager
from pprint import pformat
from typing import List, Sequence, Union, ContextManager, Optional, Any

from jiig.util.console import log_heading, log_warning, log_error, log_message, abort

from .messages import Messages
from .utility import make_list, trim_text_blocks


# TODO: Integrate Context and TopicLogger to better support general use?
class Context:
    """
    Context used by scripter code to manage and expand symbols.

    Also serves as a front end to console output functions with the added value
    of symbol expansion.
    """

    def __init__(self, debug: bool):
        self.debug = debug
        self.symbols = {}

    def update(self, **kwargs):
        try:
            # Expands in original caller's keyword argument order, which allows
            # dependencies to resolve within this one operation. (see PEP-468)
            for key, value in kwargs.items():
                self.symbols[key] = self.format(value)
        except ValueError as exc:
            self.abort(str(exc))

    def copy_symbols(self, **kwargs):
        self.symbols.update(kwargs)

    @contextmanager
    def sub_context(self, **kwargs) -> ContextManager['Context']:
        child_context = self.__class__(self.debug)
        # Parent context's symbols are already expanded.
        child_context.copy_symbols(**self.symbols)
        # Keyword argument values need expansion.
        child_context.update(**kwargs)
        yield child_context

    def format(self, text: Optional[Union[str, list, tuple]]) -> Optional[Union[str, List[str]]]:
        if text is None:
            return None
        if isinstance(text, (list, tuple)):
            return [str(item).format(**self.symbols) for item in text]
        try:
            return str(text).format(**self.symbols)
        except KeyError as key_error:
            if self.debug:
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
            self.abort(f'Bad expansion key {str(key_error)}.')

    def format_command(self,
                       command: Union[str, Sequence],
                       indent: int = None,
                       double_spaced: bool = False,
                       ) -> str:
        lines = trim_text_blocks(*make_list(command), indent=indent, double_spaced=double_spaced)
        command_text = os.linesep.join([self.format(line) for line in lines])
        return command_text

    def get(self, name) -> Optional[Any]:
        return self.symbols.get(name)

    def message(self, message: Optional[str], *args, **kwargs):
        log_message(self.format(message), *args, **kwargs)

    def warning(self, message: Optional[str], *args, **kwargs):
        log_warning(self.format(message), *args, **kwargs)

    def error(self, message: Optional[str], *args, **kwargs):
        log_error(self.format(message), *args, **kwargs)

    def abort(self, message: Optional[str], *args, **kwargs):
        abort(self.format(message), '(use --debug option for more details)', *args, **kwargs)

    def heading(self, message: Optional[str]):
        # TODO: Handle multi-level headings for scripter contexts?
        log_heading(1, self.format(message))

    def quoted(self, text: str) -> str:
        """Expands, wraps in double quotes as needed, and escapes embedded quotes."""
        expanded = self.format(text)
        if not set(expanded).intersection((' ', '"')):
            return expanded
        escaped = expanded.replace('"', '\\"')
        return f'"{escaped}"'

    def script(self,
               command_string_or_sequence: Union[str, Sequence],
               location: str = None,
               predicate: str = None,
               messages: Messages = None,
               ) -> str:
        with self.sub_context(predicate=predicate, messages=messages) as sub_context:
            output_blocks: List[str] = []
            if messages and messages.heading:
                output_blocks.append(sub_context.format_command(
                    f'echo -e "\\n[SCRIPT] === {messages.heading}"',
                ))
            if predicate:
                output_blocks.append(sub_context.format_command(
                    f'if {predicate}; then',
                ))
                indent = 4
            else:
                indent = 0
            if location:
                with sub_context.sub_context(location=sub_context.quoted(location)) as sub_sub_context:
                    output_blocks.append(
                        sub_sub_context.format_command(f'cd {location}', indent=indent))
            output_blocks.append(sub_context.format_command(
                command_string_or_sequence,
                indent=indent,
            ))
            if predicate:
                if messages and messages.skip:
                    output_blocks.append(sub_context.format_command(
                        f'''
                        else
                            echo "[SCRIPT] {messages.skip}"
                        fi
                        ''',
                    ))
                else:
                    output_blocks.append(
                        'fi',
                    )
            script_text = os.linesep.join(output_blocks)
            return script_text
