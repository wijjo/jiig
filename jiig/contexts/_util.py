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

import subprocess
from typing import Union, Sequence, Optional, Iterable, IO

from ..util import OPTIONS
from ..util.filesystem import temporary_working_folder
from ..util.general import AttrDictReadOnly
from ..util.stream import OutputFile, open_output_file

from .context import Context


def run_context_command(outer_context: Context,
                        command: Union[str, Sequence],
                        capture: bool = False,
                        unchecked: bool = False,
                        ignore_dry_run: bool = False,
                        messages: dict = None,
                        working_folder: str = None,
                        **subprocess_run_kwargs,
                        ) -> subprocess.CompletedProcess:
    """
    Run a command with support for status messages and dry-run.

    :param outer_context: context for running command
    :param command: command as string or argument list
    :param capture: capture output if True
    :param unchecked: do not check for failure
    :param ignore_dry_run: execute even if it is a dry run
    :param messages: optional status messages
    :param working_folder: temporary working folder for command execution
    :param subprocess_run_kwargs: additional subprocess.run() keyword arguments
    :return: subprocess run() result
    """
    action_messages = AttrDictReadOnly(messages or {})
    with outer_context.context(command=command) as context:

        if action_messages.before:
            context.heading(1, action_messages.before)

        context.message('command: {command}')

        if OPTIONS.dry_run and not ignore_dry_run:
            return subprocess.CompletedProcess(command, 0)

        if 'shell' not in subprocess_run_kwargs:
            subprocess_run_kwargs['shell'] = True
        if capture:
            subprocess_run_kwargs.update(capture_output=True, encoding='utf-8')

        with temporary_working_folder(context.format(working_folder)):

            proc = run_context_sub_process(context, '{command}', **subprocess_run_kwargs)

            if proc.returncode == 0:
                if action_messages.success:
                    context.message(action_messages.success)
            else:
                if action_messages.failure:
                    context.message(action_messages.failure)
                if not unchecked:
                    context.abort('Command failed.')

            if action_messages.after:
                context.message(action_messages.after)

        return proc


def run_context_sub_process(context: Context,
                            command_or_commands: Union[str, Sequence[str]],
                            **subprocess_run_kwargs,
                            ) -> subprocess.CompletedProcess:
    if isinstance(command_or_commands, (list, tuple)):
        return subprocess.run([context.format(arg) for arg in command_or_commands],
                              **subprocess_run_kwargs)
    return subprocess.run(context.format(command_or_commands),
                          **subprocess_run_kwargs)


class ContextOutputFile(OutputFile):
    """
    Special output file with additional context expansion methods and data.

    Generally not used directly. It is returned by Context.open_output_file().

    Additional data:
    - path: open file path

    Additional methods:
    - write_expanded(): write data to file with symbolic expansion
    - writelines_expanded(): write lines to file with symbolic expansion
    """

    def __init__(self, open_file: IO, context: Context, path: Optional[str]):
        """
        Context output file constructor.

        :param open_file: open file
        :param context: context with expansion symbols
        :param path: file path
        """
        super().__init__(open_file, path)
        self.context = context

    def write_expanded(self, s: str) -> int:
        """
        Write data to file with symbolic expansion.

        See IO.write().

        :param s: text to write
        :return: same as return from IO.write()
        """
        return self.open_file.write(self.context.format(s))

    def writelines_expanded(self, lines: Iterable[str]):
        """
        Write lines to file with symbolic expansion.

        See IO.writelines().

        :param lines: lines to write
        """
        return self.open_file.writelines([self.context.format(line) for line in lines])


def open_context_output_file(context: Context,
                             path: str,
                             binary: bool = False,
                             keep_temporary: bool = False,
                             ) -> ContextOutputFile:
    with Context(context, path=path) as sub_context:
        opened_file_data = open_output_file(sub_context.s.path,
                                            binary=binary,
                                            keep_temporary=keep_temporary,
                                            create_parent_folder=True)
        return ContextOutputFile(opened_file_data.open_file, context, opened_file_data.path)
