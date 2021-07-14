"""ActionContext program execution API."""

import os
import subprocess
from typing import Sequence, Union, Tuple, Optional, List

from ..util import OPTIONS
from ..util.general import AttrDictReadOnly
from ..util.network import format_host_string
from ..util.script import Script

from .context import Context
from ._util import run_context_command, run_context_sub_process, open_context_output_file


# Precedes the script body in generated script files.
SCRIPT_PREAMBLE = '''
#!/usr/bin/env bash

set -e%s

echo "::: ${{BASH_SOURCE[0]}} :::"
'''.strip()


class ActionContextRunAPI:

    def __init__(self, context: Context):
        self.context = context

    def command(self,
                command: Union[str, Sequence],
                capture: bool = False,
                unchecked: bool = False,
                ignore_dry_run: bool = False,
                messages: dict = None,
                working_folder: str = None,
                **subprocess_run_kwargs,
                ) -> subprocess.CompletedProcess:
        """
        Run a command with support for messages, and dry-run.

        :param command: command as string or argument list
        :param capture: capture output if True
        :param unchecked: do not check for failure
        :param ignore_dry_run: execute even if it is a dry run
        :param messages: messages to add to output
        :param working_folder: temporary working folder for command execution
        :param subprocess_run_kwargs: additional subprocess.run() keyword arguments
        :return: subprocess run() result
        """
        return run_context_command(self.context,
                                   command,
                                   capture=capture,
                                   unchecked=unchecked,
                                   ignore_dry_run=ignore_dry_run,
                                   messages=messages,
                                   working_folder=working_folder,
                                   **subprocess_run_kwargs)

    def pipe(self, raw_command: Union[str, List]) -> str:
        """
        Run command and capture output.

        :param raw_command: command to expand and run
        :return: command output block
        """
        proc = self.command(raw_command, capture=True)
        return proc.stdout.strip()

    def pipe_lines(self, raw_command: Union[str, List]) -> List[str]:
        """
        Run command and capture output as a list of lines.

        :param raw_command: command to expand and run
        :return: command output lines
        """
        return self.pipe(raw_command).split(os.linesep)

    def sub_process(self,
                    command_or_commands: Union[str, Sequence[str]],
                    **subprocess_run_kwargs,
                    ) -> subprocess.CompletedProcess:
        """
        Context-based front end to subprocess.run() with text expansion.

        :param command_or_commands: command string or sequence
        :param subprocess_run_kwargs: additional keyword arguments to subprocess.run()
        :return: subprocess.run() CompletedProcess return value
        """
        return run_context_sub_process(self.context, command_or_commands, **subprocess_run_kwargs)

    def _get_host_user(self,
                       host: Optional[str],
                       user: Optional[str],
                       host_string: Optional[str],
                       ) -> Tuple[str, str]:
        if host_string:
            user_host = host_string.split('@', maxsplit=1)
            if len(user_host) == 2:
                return user_host[1], user_host[0]
            self.context.error(f'Bad host_string value: {host_string}')
        return host, user

    def script(self,
               script_text_or_object: Union[str, Sequence[str], Script],
               script_path: str = None,
               host: str = None,
               user: str = None,
               host_string: str = None,
               messages: dict = None,
               unchecked: bool = False,
               ignore_dry_run: bool = False,
               ) -> subprocess.CompletedProcess:
        """
        Execute a local or remote Bash script file.

        The saved script file defaults to being temporary, but the caller can
        specify a permanent path via script_path to override that behavior.

        :param script_text_or_object: script body text from string, list or Script object
        :param script_path: optional script output path (temporary if it contains '?')
        :param host: optional target host for remote command
        :param user: optional target host user name for remote command
        :param host_string: alternate user@host form for host and user
        :param messages: optional status messages
        :param unchecked: do not check return code for success
        :param ignore_dry_run: execute even if it is a dry run
        :return: subprocess.CompletedProcess result
        """
        action_messages = AttrDictReadOnly(messages or {})

        dry_run = OPTIONS.dry_run and not ignore_dry_run

        host, user = self._get_host_user(host, user, host_string)

        if host:
            command = 'ssh -qt {target_host_string} bash {script_file}'
            deploy_command = 'scp {script_file} {target_host_string}:{script_file}'
        else:
            command = '/bin/bash {script_file}'
            deploy_command = None

        # Outer context has immediately-resolvable symbols, e.g. expanded for file output.
        with self.context.context(target_host=host,
                                  target_user=user,
                                  target_host_string=format_host_string(host=host, user=user),
                                  script_preamble=_get_script_preamble(),
                                  script_body=_get_script_body(script_text_or_object),
                                  output_label='[host={target_host}] ' if host else ''
                                  ) as script_context:

            with open_context_output_file(script_context,
                                          script_path or '/tmp/scripter_?.sh',
                                          ) as output_file:

                # Inner context symbols needed the script file path to resolve.
                with script_context.context(script_file=output_file.path,
                                            command=command,
                                            deploy_command=deploy_command,
                                            ) as run_context:

                    _script_start(run_context, action_messages)

                    if OPTIONS.debug or dry_run:
                        run_context.heading(1, 'Script {script_file} (begin)')
                        run_context.message('{script_preamble}{nl}{nl}{script_body}')
                        run_context.heading(1, 'Script {script_file} (end)')

                    # Write script file.
                    output_file.write_expanded('{script_preamble}{nl}{nl}{script_body}')
                    output_file.flush()
                    run_context.message('Script saved: {script_file}')
                    if OPTIONS.pause:
                        input('Press Enter to continue:')

                    if dry_run:
                        return subprocess.CompletedProcess(command, 0)

                    # Deploy the script?
                    if deploy_command:
                        proc = run_context_sub_process(run_context, '{deploy_command}', shell=True)
                        if proc.returncode != 0:
                            run_context.abort('Failed to deploy script.')

                    # Run the script.
                    run_context.message('command: {command}')
                    run_context.heading(1, '{output_label}output (start)')
                    proc = run_context_sub_process(run_context, '{command}', shell=True)
                    run_context.heading(1, '{output_label}output (end)')

                    # Display final messages and handle failure.
                    return _script_finish(run_context, proc, unchecked, action_messages)

    def script_code(self,
                    script_text_or_object: Union[str, Sequence[str], Script],
                    host: str = None,
                    user: str = None,
                    host_string: str = None,
                    messages: dict = None,
                    unchecked: bool = False,
                    ignore_dry_run: bool = False,
                    ) -> subprocess.CompletedProcess:
        """
        Execute a local or remote Bash script without saving to a file.

        Note that direct script execution is primarily provided so that a host
        user without key-based SSH connections can avoid triggering an extra
        password prompt for a separate deploy command, e.g. scp.

        NB: Be aware that quoting and escaping is currently simplistic and will
        not handle all scenarios with embedded quotes. The safest thing to do is
        to always use double quotes for internal command arguments and to escape
        any quotes within those argument strings. The `direct` option may add
        complications because of the further quoting needed to pass the script
        as a single argument to bash on the SSH command line.

        TODO: Reduce or eliminate the caveats related to quoting and escaping.

        :param script_text_or_object: script body text from string, list or Script object
        :param host: optional host for remote command
        :param user: optional user name for remote command
        :param host_string: alternate user@host form for host and user
        :param messages: optional status messages
        :param unchecked: do not check return code for success
        :param ignore_dry_run: execute even if it is a dry run
        :return: subprocess.CompletedProcess result
        """
        action_messages = AttrDictReadOnly(messages or {})

        dry_run = OPTIONS.dry_run and not ignore_dry_run

        host, user = self._get_host_user(host, user, host_string)

        if host:
            command = 'ssh -qt {host_string} bash -c "\'{script_body}\'"'
            quoted = True
        else:
            command = 'bash -c "{script_body}"'
            quoted = False

        with self.context.context(host=host,
                                  user=user,
                                  host_string=format_host_string(host=host, user=user),
                                  script_body=_get_script_body(script_text_or_object, quoted=quoted),
                                  command=command,
                                  output_label='[host={host}] ' if host else ''
                                  ) as sub_context:

            _script_start(sub_context, action_messages)

            if OPTIONS.debug or dry_run:
                sub_context.heading(1, 'Script code (begin)')
                sub_context.message('{script_body}')
                sub_context.heading(1, 'Script code (end)')

            if dry_run:
                return subprocess.CompletedProcess(command, 0)

            if OPTIONS.pause:
                input('Press Enter to continue:')

            sub_context.message('command: {command}')

            # Run the script.
            sub_context.heading(1, '{output_label}output (start)')
            proc = run_context_sub_process(sub_context, '{command}', shell=True)
            sub_context.heading(1, '{output_label}output (end)')

            return _script_finish(sub_context, proc, unchecked, action_messages)


def _get_script_preamble():
    return SCRIPT_PREAMBLE % ('x' if OPTIONS.debug else '')


def _get_script_body(script_text_or_object: Union[str, Sequence[str], Script],
                     quoted: bool = False,
                     ) -> str:
    if isinstance(script_text_or_object, Script):
        text = script_text_or_object.get_script_body()
    elif isinstance(script_text_or_object, (list, tuple)):
        text = os.linesep.join(script_text_or_object)
    else:
        text = script_text_or_object
    return text.replace("'", "\\'") if quoted else text


def _script_start(context: Context, action_messages: AttrDictReadOnly):
    if action_messages.before:
        context.message(action_messages.before)


def _script_finish(context: Context,
                   proc: subprocess.CompletedProcess,
                   unchecked: bool,
                   action_messages: AttrDictReadOnly,
                   ) -> subprocess.CompletedProcess:
    if proc.returncode == 0:
        if action_messages.success:
            context.message(action_messages.success)
    else:
        if action_messages.failure:
            context.message(action_messages.failure)
        if not unchecked:
            context.abort('Script execution failed.')
    if action_messages.after:
        context.message(action_messages.after)
    return proc
