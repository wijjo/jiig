"""
Scripter script.
"""

import os
from contextlib import contextmanager
from typing import List, ContextManager, Union, Sequence

from ..util.general import make_list, trim_text_blocks, AttrDictReadOnly


class Script:
    """Used to build a script piecemeal and then execute it."""

    indent_spaces = 4

    def __init__(self,
                 unchecked: bool = False,
                 run_by_root: bool = False,
                 blocks: List[str] = None,
                 ):
        """
        Construct script.

        :param unchecked: do not check return code if True
        :param run_by_root: script will be run by root user (don't need sudo)
        :param blocks: initial script blocks (not typically used)
        """
        self.unchecked = unchecked
        self.run_by_root = run_by_root
        self.blocks: List[str] = blocks if blocks is not None else []
        self.indent_level = 0

    def _add(self, *blocks: str, double_spaced: bool = False):
        lines = trim_text_blocks(*blocks,
                                 indent=self.indent_level * self.indent_spaces,
                                 double_spaced=double_spaced)
        self.blocks.append(os.linesep.join(lines))

    @contextmanager
    def indent(self) -> ContextManager:
        """Indent lines added within `with` statement block."""
        self.indent_level += 1
        yield
        self.indent_level -= 1

    @contextmanager
    def block(self,
              predicate: str = None,
              location: str = None,
              messages: dict = None,
              ) -> ContextManager:
        """
        Wrap a block with optional predicate condition and status messages.

        :param predicate: predicate condition (for if statement)
        :param location: optional temporary working folder
        :param messages: optional before, after, or skip messages
        """
        action_messages = AttrDictReadOnly(messages or {})
        if predicate:
            self._add(f'if {predicate}; then')
            self.indent_level += 1
        if action_messages.before:
            self._add(f'echo -e "\\n=== {action_messages.before}"')
        if location:
            self._add(f'pushd {self._quoted(location)} > /dev/null')
        yield
        if action_messages.after:
            self._add(f'echo -e "\\n=== {action_messages.after}"')
        if location:
            self._add(f'popd > /dev/null')
        if predicate:
            self.indent_level -= 1
            if action_messages.skip:
                self._add('else')
                with self.indent():
                    self._add(f'echo "{action_messages.skip}"')
            self._add('fi')

    @staticmethod
    def _quoted(text: str) -> str:
        if not set(text).intersection((' ', '"')):
            return text
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'

    def action(self,
               command_string_or_sequence: Union[str, Sequence],
               messages: dict = None,
               ):
        """
        Add script action command(s) and display optional status messages.

        :param command_string_or_sequence: command or commands
        :param messages: optional status messages
        """
        # TODO: Handle message quoting/escaping for echo statements.
        action_messages = AttrDictReadOnly(messages or {})
        commands = make_list(command_string_or_sequence)
        if commands:
            self._add(*commands)
            if action_messages.success and action_messages.failure:
                self._add('if [[ $? -eq 0 ]]; then')
                with self.indent():
                    self._add(f'echo "{action_messages.success}"')
                self._add('else')
                with self.indent():
                    self._add(f'echo "{action_messages.failure}"')
                self._add('fi')
            elif action_messages.success and not action_messages.failure:
                self._add('if [[ $? -eq 0 ]]; then')
                with self.indent():
                    self._add(f'echo "{action_messages.success}"')
                self._add('fi')
            elif not action_messages.success and action_messages.failure:
                self._add('if [[ $? -ne 0 ]]; then')
                with self.indent():
                    self._add(f'echo "{action_messages.failure}"')
                self._add('fi')

    def working_folder(self, folder: str, messages: dict = None):
        """
        Set working folder in script.

        :param folder: folder switch to
        :param messages: optional status messages
        """
        self.action(f'cd {folder}', messages=messages)

    def _wrap_command(self, command: str, need_root: bool = False) -> str:
        """
        Prefix with "sudo" as needed.

        :param command: command to wrap, e.g. with sudo
        :param need_root: prefix with sudo if True
        :return: command with sudo prefix (if the script isn't being run by root)
        """
        return f'sudo {command}' if need_root and not self.run_by_root else command

    def get_script_body(self) -> str:
        """
        Produce script body based on previously-formatted blocks.

        IMPORTANT: Clears out previous blocks to start building a new script.

        Does not include "shebang" line or shell options setting.

        :return: script body text
        """
        body_text = f'{os.linesep}{os.linesep}'.join(self.blocks)
        self.blocks = []
        return body_text
