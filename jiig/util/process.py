"""
Process management utilities.
"""

import os
import shlex
import subprocess
from typing import Text, List, Dict, Optional

from .log import abort, log_message
from .options import OPTIONS

# Operators to leave unchanged when quoting shell arguments.
SHELL_OPERATORS = ['<', '>', '|', '&&', '||', ';']


def shell_quote_arg(arg: Text) -> Text:
    """
    Quote a normal shell argument, but leave operators unchanged.

    :param arg: shell argument
    :return: possibly-quoted argument
    """
    return arg if arg in SHELL_OPERATORS else shlex.quote(str(arg))


def shell_command_string(command: Text, *args) -> Text:
    """
    Format a shell command string with appropriate argument quoting.

    :param command: command (without arguments)
    :param args: trailing arguments
    :return: command as a single string with quoted arguments
    """
    return ' '.join([shell_quote_arg(str(arg)) for arg in [command] + list(args)])


def shell_quote_path(path: str) -> str:
    """
    Wrap path in double quotes as needed.

    Does not handle everything. For one, it intentionally does not quote ~.

    :param path: input path
    :return: possibly-quoted path
    """
    if path and path[0] != '"' and set(path).intersection(' \t<>!$`*?(){}|;'):
        return f'"{path}"'
    return path


def run(cmd_args: List[Text],
        unchecked: bool = False,
        replace_process: bool = False,
        working_folder: Text = None,
        env: Dict = None,
        host: Text = None,
        shell: bool = False,
        run_always: bool = False,
        quiet: bool = False,
        capture: bool = False,
        ) -> Optional[subprocess.CompletedProcess]:
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
    :return: CompletedProcess object if the command was executed
    """
    if not cmd_args:
        abort('Called run() without a command.')
    if not isinstance(cmd_args, (tuple, list)):
        abort('Called run() with a non-list/tuple.', cmd_args=cmd_args)
    if host:
        if shell or env or working_folder:
            abort('Remote run() command, i.e. with "host" specified, may not'
                  ' use "shell", "env", or "working_folder" keywords.',
                  cmd_args=cmd_args)
    # The command string for display or shell execution.
    cmd_string = shell_command_string(*cmd_args)
    # Adjust remote command to run through SSH.
    if host:
        cmd_args = ['ssh', host] + cmd_args
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
        return None
    # Generate the command run environment.
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    # Set a temporary working folder, if specified.
    if working_folder:
        if not os.path.isdir(working_folder):
            abort('Desired working folder does not exist', working_folder)
        restore_folder = os.getcwd()
        os.chdir(working_folder)
    else:
        restore_folder = None
    # Run the command with process replacement.
    if replace_process:
        os.execlp(cmd_args[0], *cmd_args)
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
            return subprocess.run(cmd_args, **kwargs)
        except subprocess.CalledProcessError as exc:
            abort('Command failed.', cmd_string, exc)
        except FileNotFoundError as exc:
            abort('Command not found.', cmd_string, exc)
    finally:
        if restore_folder:
            os.chdir(restore_folder)


def run_shell(cmd_args: List[Text],
              unchecked: bool = False,
              working_folder: Text = None,
              replace_process: bool = False,
              run_always: bool = False):
    return run(cmd_args,
               unchecked=unchecked,
               replace_process=replace_process,
               working_folder=working_folder,
               shell=True,
               run_always=run_always)


def run_remote(host: Text,
               cmd_args: List[Text],
               unchecked: bool = False,
               replace_process: bool = False,
               run_always: bool = False):
    return run(cmd_args,
               host=host,
               unchecked=unchecked,
               replace_process=replace_process,
               run_always=run_always)
