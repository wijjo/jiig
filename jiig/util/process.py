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

"""
Process management utilities.
"""

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .log import abort, log_message
from .options import OPTIONS

# Operators to leave unchanged when quoting shell arguments.
SHELL_OPERATORS = ['<', '>', '|', '&&', '||', ';']
# Regular expression for finding characters requiring quoting.
SHELL_QUOTED_REGEX = re.compile(r'[\s"\\;<>{}()\[\]|&]')
# Characters that need to be escaped inside a double-quoted string.
SHELL_ESCAPED_REGEX = re.compile(r'"')


def shell_quote_arg(arg: str) -> str:
    """
    Quote a normal shell argument, but leave operators unchanged.

    :param arg: shell argument
    :return: possibly-quoted argument
    """
    return arg if arg in SHELL_OPERATORS else shlex.quote(str(arg))


def shell_command_string(command: str, *args) -> str:
    """
    Format a shell command string with appropriate argument quoting.

    :param command: command (without arguments)
    :param args: trailing arguments
    :return: command as a single string with quoted arguments
    """
    return ' '.join([shell_quote_arg(str(arg)) for arg in [command] + list(args)])


def shell_quote_path(path: str | Path) -> str:
    """
    Wrap path in double quotes as needed.

    Does not handle everything. For one, it intentionally does not quote ~.

    :param path: input path
    :return: possibly-quoted path
    """
    path_string = str(path)
    if (path_string and path_string[0] != '"'
            and set(path_string).intersection(' \t<>!$`*?(){}|;')):
        return f'"{path}"'
    return path_string


def run(cmd_args: list,
        unchecked: bool = False,
        replace_process: bool = False,
        working_folder: str | Path = None,
        env: dict = None,
        host: str = None,
        shell: bool = False,
        run_always: bool = False,
        quiet: bool = False,
        capture: bool = False,
        ) -> subprocess.CompletedProcess:
    """
    Run a shell command.

    Front end to subprocess.run() that adds support for some Jiig-specific
    options. Uses os.execl() when replacing the process.

    Also supports SSH remote execution.

    :param cmd_args: raw argument list
    :param unchecked: return when an error occurs instead of aborting if True
    :param replace_process: replace current process if True
    :param working_folder: folder to change to before running command
    :param env: environment variables passed to command process
    :param host: host for remote execution
    :param shell: run inside a new shell process if True
    :param run_always: execute even during a dry run if True
    :param quiet: suppress normal messages if True
    :param capture: capture standard output if True
    :return: CompletedProcess object
    """
    if not cmd_args:
        abort('Called run() without a command.')
    if not isinstance(cmd_args, (tuple, list)):
        abort('Called run() with a non-list/tuple.', cmd_args=cmd_args)
    cmd_strings = [str(arg) for arg in cmd_args]
    if host:
        if shell or env or working_folder:
            abort('Remote run() command, i.e. with "host" specified, may not'
                  ' use "shell", "env", or "working_folder" keywords.',
                  cmd_args=cmd_args)
    # The command string for display or shell execution.
    cmd_string = shell_command_string(*cmd_strings)
    # Adjust remote command to run through SSH.
    if host:
        cmd_strings = ['ssh', host] + cmd_strings
    # Log message about impending command and run options.
    message_data = {}
    if env:
        message_data['environment'] = ' '.join([
            '{}={}'.format(name, shlex.quote(value))
            for name, value in env.items()])
    if host:
        message_data['host'] = host
    if replace_process:
        message_data['exec'] = 'yes'
    if quiet:
        message_data['verbose'] = True
    log_message('Run command.', cmd_string, **message_data)
    # A dry run can stop here, before taking real action.
    if OPTIONS.dry_run and not run_always:
        return subprocess.CompletedProcess(cmd_strings, 0)
    # Generate the command run environment.
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    # Set a temporary working folder, if specified.
    if working_folder:
        working_folder = Path(working_folder)
        if not working_folder.is_dir():
            abort('Desired working folder does not exist', working_folder)
        restore_folder = os.getcwd()
        os.chdir(working_folder)
    else:
        restore_folder = None
    # Run the command with process replacement.
    if replace_process:
        os.execlp(cmd_strings[0], *cmd_strings)
    # Or run the command and continue.
    try:
        try:
            kwargs = dict(
                check=not unchecked,
                shell=shell,
                env=run_env,
                capture_output=capture,
            )
            if capture:
                kwargs['encoding'] = 'utf-8'
            return subprocess.run(cmd_strings, **kwargs)
        except subprocess.CalledProcessError as exc:
            abort('Command failed.', cmd_string, exc)
        except FileNotFoundError as exc:
            abort('Command not found.', cmd_string, exc)
    finally:
        if restore_folder:
            os.chdir(restore_folder)


def run_shell(cmd_args: list,
              unchecked: bool = False,
              replace_process: bool = False,
              working_folder: str | Path = None,
              run_always: bool = False,
              ) -> subprocess.CompletedProcess:
    """
    Run command using shell.

    :param cmd_args: raw argument list
    :param unchecked: return when an error occurs instead of aborting if True
    :param replace_process: replace current process if True
    :param working_folder: folder to change to before running command
    :param run_always: execute even during a dry run if True
    :return: CompletedProcess object
    """
    return run(cmd_args,
               unchecked=unchecked,
               replace_process=replace_process,
               working_folder=working_folder,
               shell=True,
               run_always=run_always)


def run_remote(host: str,
               cmd_args: list,
               unchecked: bool = False,
               replace_process: bool = False,
               run_always: bool = False):
    """
    Run command on remote host.

    :param cmd_args: raw argument list
    :param host: host for remote execution
    :param unchecked: return when an error occurs instead of aborting if True
    :param replace_process: replace current process if True
    :param run_always: execute even during a dry run if True
    :return: CompletedProcess object
    """
    return run(cmd_args,
               host=host,
               unchecked=unchecked,
               replace_process=replace_process,
               run_always=run_always)


def pipe(command: list) -> list[str]:
    """
    Run command and receive output.

    :param command: command to execute as string or list
    :return: output lines
    """
    proc = run(command, capture=True)
    if not proc.stdout:
        return []
    return proc.stdout.strip().split(os.linesep)


def escape_line_endings(input_string: str) -> str:
    """
    Escape line ending characters.

    :param input_string: string to scan for line endings
    :return: string with escaped line endings
    """
    return input_string.replace('\n', r'\n').replace('\r', r'\r')


def simple_shell_quote(value: Any,
                       literal: bool = False,
                       unquoted: bool = False,
                       ) -> str:
    """
    Simplistic shell argument quoting.

    Literals are single-quoted by shlex.quote(). Otherwise double quotes and
    internal escapes are added as required.

    :param value: value to quote (after converting to a string as needed)
    :param literal: use single quotes to prevent shell expansion of '$...', etc.
    :param unquoted: disable quoting if True
    :return: quoted/escaped text
    """
    text = str(value)
    if unquoted:
        return text
    # Literals go in single quotes, which shlex.quote() can handle.
    if literal:
        return shlex.quote(escape_line_endings(text))
    # Nothing to do if nothing requires quoting.
    if not SHELL_QUOTED_REGEX.search(text):
        return text
    # Search for all escaped characters and inject preceding backslashes.
    parts: list[str] = []
    pos = 0
    for found_escaped_character in SHELL_ESCAPED_REGEX.finditer(text):
        end_pos = found_escaped_character.end()
        if end_pos - 1 > pos:
            parts.append(text[pos:end_pos - 1])
        parts.append('\\')
        parts.append(text[end_pos - 1])
        pos = end_pos
    if pos < len(text):
        parts.append(text[pos:])
    final_text = ''.join(parts)
    return f'"{final_text}"'


def simple_shell_quote_arguments(args: Sequence) -> str:
    """
    Simplistic shell argument quoting applied to sequence of arguments.

    :param args: raw command arguments
    :return: command string with quoted arguments
    """
    return ' '.join(simple_shell_quote(arg) for arg in args)
