"""ActionContext file manipulation API."""
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

import os
import re
import shutil
from typing import Iterator, IO

from ..util.stream import open_input_file
from ..util.general import AttrDictReadOnly
from ..util.text import trim_text_blocks, plural

from .context import Context
from ._util import run_context_command, ContextOutputFile, open_context_output_file


class ActionContextFileAPI:

    def __init__(self, context: Context):
        self.context = context

    def open_input(self, path: str, binary: bool = False) -> IO:
        """
        Convenient layer over open() with better defaults and symbol expansion.

        Provides an IO-compatible object, usable in a `with` statement, that
        performs symbolic text expansion.

        :param path: file path, possibly including a '?' marker to create a temporary file
        :param binary: open the file in binary mode (defaults to utf-8 text)
        :return: open file object, usable in a `with` statement for automatic closing
        """
        return open_input_file(self.context.format(path), binary=binary)

    def open_output(self,
                    path: str,
                    binary: bool = False,
                    keep_temporary: bool = False,
                    ) -> ContextOutputFile:
        """
        Uses stream.open_output_file to open a temporary or permanent file.

        Provides an IO-compatible object, usable in a `with` statement, that
        performs symbolic text expansion.

        :param path: file path, possibly including a '?' marker to create a temporary file
        :param binary: open the file in binary mode (defaults to utf-8 text)
        :param keep_temporary: do not delete temporary file if True
        :return: open file object, usable in a `with` statement for automatic closing
        """
        return open_context_output_file(self.context,
                                        path,
                                        binary=binary,
                                        keep_temporary=keep_temporary)

    def grep(self, path: str, raw_pattern: str, case_insensitive: bool = False) -> Iterator[str]:
        """
        Search for a regular expression in a file.

        :param path: file path
        :param raw_pattern: regular expression pattern to expand, compile, search for
        :param case_insensitive: perform a case-insensitive search
        :return: found line iterator
        """
        expanded_path = self.context.format(path)
        pattern = self.context.format(raw_pattern)
        if os.path.exists(expanded_path):
            compile_option_args = [re.IGNORECASE] if case_insensitive else []
            compiled_pattern = re.compile(pattern, *compile_option_args)
            with open(os.path.expanduser(expanded_path), encoding='utf-8') as open_file:
                for line in open_file.readlines():
                    if compiled_pattern.search(line):
                        yield line

    def contains(self, path: str, raw_pattern: str, case_insensitive: bool = False) -> bool:
        """
        Search for a regular expression in a file and return True if found.

        :param path: file path
        :param raw_pattern: regular expression pattern to expand, compile, search for
        :param case_insensitive: perform a case-insensitive search
        :return: True if the pattern was found
        """
        return bool(list(self.grep(path, raw_pattern, case_insensitive=case_insensitive)))

    def exists(self, *paths: str):
        """
        Check that one or more files exist and abort if anything is missing.

        :param paths: file paths to check
        """
        with self.context.context(paths=paths) as context:
            missing = [path for path in context.s.paths if not os.path.exists(path)]
            if missing:
                context.abort(f'Required {plural("file", missing)} missing:', *missing)

    def add_text(self,
                 path: str,
                 *blocks: str,
                 backup: bool = True,
                 permissions: str = None,
                 exists_pattern: str = None,
                 messages: dict = None,
                 keep_indent: bool = False,
                 ):
        """
        Append text block(s) to file as needed.

        Can be gated by checking for a regular expression existence pattern.

        :param path: file path (will be expanded)
        :param blocks: text block(s) to expand and append if required
        :param backup: backup the file if True
        :param permissions: optional permissions to apply
        :param exists_pattern: optional regular expression check if missing
        :param messages: optional status messages
        :param keep_indent: preserve indentation if True
        """
        action_messages = AttrDictReadOnly(messages or {})
        expanded_path = self.context.format(path)
        if action_messages.before:
            self.context.heading(1, action_messages.before)
        exists = os.path.exists(expanded_path)
        if exists_pattern and self.contains(expanded_path, exists_pattern):
            if action_messages.skip:
                self.context.message(action_messages.skip)
            return
        if backup:
            if os.path.exists(expanded_path):
                shutil.copy(path, f'{expanded_path}.backup')
        with open(path, 'a', encoding='utf-8') as open_file:
            if exists:
                open_file.write(os.linesep)
            for raw_line in trim_text_blocks(*blocks, keep_indent=keep_indent):
                line = self.context.format(raw_line)
                open_file.write(line)
                open_file.write(os.linesep)
        if permissions is not None:
            run_context_command(self.context, f'chmod {permissions} {expanded_path}')
        if action_messages.after:
            self.context.message(action_messages.after)
