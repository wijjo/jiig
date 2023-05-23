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

"""Shell script builder."""

import os
from contextlib import (
    AbstractContextManager,
    contextmanager,
)
from typing import Sequence

from .collections import (
    AttributeDictionary,
    make_list,
)
from .text.blocks import trim_text_blocks


class Script:
    """Used to build a shell script piecemeal and then execute it."""

    indent_spaces = 4

    def __init__(self,
                 unchecked: bool = False,
                 run_by_root: bool = False,
                 blocks: list[str] = None,
                 ):
        """
        Construct script.

        Args:
            unchecked: do not check return code if True
            run_by_root: script will be run by root user (don't need sudo)
            blocks: initial script blocks (not typically used)
        """
        self.unchecked = unchecked
        self.run_by_root = run_by_root
        self.blocks: list[str] = blocks if blocks is not None else []
        self.indent_level = 0

    def _add(self, *blocks: str, double_spaced: bool = False):
        lines = trim_text_blocks(*blocks,
                                 indent=self.indent_level * self.indent_spaces,
                                 double_spaced=double_spaced)
        self.blocks.append(os.linesep.join(lines))

    @contextmanager
    def indent(self) -> AbstractContextManager:
        """Indent lines added within `with` statement block."""
        self.indent_level += 1
        yield
        self.indent_level -= 1

    @contextmanager
    def block(self,
              predicate: str = None,
              location: str = None,
              messages: dict = None,
              ) -> AbstractContextManager:
        """Wrap a block with optional predicate condition and status messages.

        Args:
            predicate: predicate condition (for if statement)
            location: optional temporary working folder
            messages: optional before, after, or skip messages
        """
        action_messages = AttributeDictionary.new(messages or {}, read_only=True)
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
               command_string_or_sequence: str | Sequence,
               messages: dict = None,
               ):
        """Add script action command(s) and display optional status messages.

        Args:
            command_string_or_sequence: command or commands
            messages: optional success or failure status messages
        """
        # TODO: Handle message quoting/escaping for echo statements.
        action_messages = AttributeDictionary.new(messages or {}, read_only=True)
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
        """Set working folder in script.

        Args:
            folder: folder switch to
            messages: optional status messages
        """
        self.action(f'cd {folder}', messages=messages)

    def wrap_command(self, command: str, need_root: bool = False) -> str:
        """Prefix with "sudo" as needed.

        Args:
            command: command to wrap, e.g. with sudo
            need_root: prefix with sudo if True

        Returns:
            command with sudo prefix (if the script isn't being run by root)
        """
        return f'sudo {command}' if need_root and not self.run_by_root else command

    def get_script_body(self) -> str:
        """Produce script body based on previously-formatted blocks.

        IMPORTANT: Clears out previous blocks to start building a new script.

        Does not include "shebang" line or shell options setting.

        Returns:
            script body text
        """
        body_text = f'{os.linesep}{os.linesep}'.join(self.blocks)
        self.blocks = []
        return body_text
