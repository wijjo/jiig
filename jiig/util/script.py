"""
Scripter script.
"""

import os
import sys
from contextlib import contextmanager
from subprocess import CompletedProcess, run
from tempfile import NamedTemporaryFile
from typing import List, ContextManager, Union, Sequence, Optional, TypeVar

from .action_messages import ActionMessages
from .context import Context
from .general import make_list
from .options import Options

T_script = TypeVar('T_script', bound='Script')


class Script:
    """Used to build a script piecemeal and then execute it."""

    def __init__(self,
                 context: Context,
                 unchecked: bool = False,
                 run_by_root: bool = False,
                 blocks: List[str] = None,
                 ):
        """
        Construct script.

        :param context: text expansion context
        :param unchecked: do not check return code if True
        :param run_by_root: script will be run by root user (don't need sudo)
        :param blocks: initial script blocks (not typically used)
        """
        self.unchecked = unchecked
        self.run_by_root = run_by_root
        self.blocks: List[str] = blocks if blocks is not None else []
        self.context = context.create_child_context()

    def update(self, **kwargs):
        self.context.update(**kwargs)

    def copy_symbols(self, **kwargs):
        self.context.copy_symbols(**kwargs)

    @contextmanager
    def sub_script(self, **kwargs) -> ContextManager[T_script]:
        yield self.__class__(self.context.create_child_context(**kwargs),
                             unchecked=self.unchecked,
                             run_by_root=self.run_by_root,
                             blocks=self.blocks)

    def add_block(self,
                  command_string_or_sequence: Union[str, Sequence],
                  location: str = None,
                  predicate: str = None,
                  messages: dict = None,
                  ):
        self.blocks.append(
            self.format_script_block(
                command_string_or_sequence,
                location=location,
                predicate=predicate,
                messages=messages,
            )
        )

    def action(self,
               command: Union[str, Sequence],
               location: str = None,
               predicate: str = None,
               messages: dict = None,
               ):
        self.blocks.append(
            self.format_script_block(
                command,
                predicate=predicate,
                location=location,
                messages=messages,
            )
        )

    @contextmanager
    def temporary_working_folder(self,
                                 folder: str,
                                 messages: dict = None,
                                 ) -> ContextManager[None]:
        with self.sub_script(folder=folder) as sub_script:
            sub_script.add_block('pushd {folder} > /dev/null', messages=messages)
            yield
            sub_script.add_block('popd > /dev/null')

    def _wrap_command(self, command: str, need_root: bool = False) -> str:
        """
        Prefix, e.g. with "sudo", as needed.

        :param command: command to wrap, e.g. with sudo
        :param need_root: prefix with sudo if True
        :return: command with sudo prefix (if the script isn't being run by root)
        """
        return f'sudo {command}' if need_root and not self.run_by_root else command

    @classmethod
    def format_host_string(cls, host: str = None, user: str = None) -> Optional[str]:
        if not host:
            return None
        if not user:
            return host
        return f'{user}@{host}' if user else host

    def format_script_block(self,
                            command_string_or_sequence: Union[str, Sequence],
                            location: str = None,
                            predicate: str = None,
                            messages: dict = None,
                            ) -> str:
        """
        Format a shell script given one or more commands.

        :param command_string_or_sequence: command or commands to include in script
        :param location: optional target directory to switch to
        :param predicate: optional predicate to test before executing commands
        :param messages: messages to display before, after, and during
        :return: formatted script text
        """
        # TODO: Handle message quoting/escaping for echo statements.
        action_messages = ActionMessages.from_dict(messages)

        output_blocks: List[str] = []
        if action_messages.before:
            output_blocks.append(
                self.context.format_blocks(
                    f'echo -e "\\n=== {action_messages.before}"',
                )
            )
        if predicate:
            output_blocks.append(
                self.context.format_blocks(
                    f'if {predicate}; then',
                )
            )
            indent = 4
        else:
            indent = 0
        if location:
            output_blocks.append(
                self.context.format_blocks(
                    f'cd {self.context.format_quoted(location)}',
                    indent=indent,
                )
            )
        commands = make_list(command_string_or_sequence)
        if commands:
            output_blocks.append(
                self.context.format_blocks(
                    *commands,
                    indent=indent,
                )
            )
            if action_messages.success and action_messages.failure:
                output_blocks.append(
                    self.context.format_blocks(
                        f'''
                        if [[ $? -eq 0 ]]; then
                            echo "{self.context.format(action_messages.success)}"
                        else
                            echo "{self.context.format(action_messages.failure)}"
                        fi
                        ''',
                        indent=indent,
                    )
                )
            elif action_messages.success and not action_messages.failure:
                output_blocks.append(
                    self.context.format_blocks(
                        f'''
                        if [[ $? -eq 0 ]]; then
                            echo "{self.context.format(action_messages.success)}"
                        fi
                        ''',
                        indent=indent,
                    )
                )
            elif not action_messages.success and action_messages.failure:
                output_blocks.append(
                    self.context.format_blocks(
                        f'''
                        if [[ $? -ne 0 ]]; then
                            echo "{self.context.format(action_messages.failure)}"
                        fi
                        ''',
                        indent=indent,
                    )
                )
        if predicate:
            if action_messages.skip:
                output_blocks.append(
                    self.context.format_blocks(
                        f'''
                        else
                            echo "{self.context.format(action_messages.skip)}"
                        fi
                        ''',
                    )
                )
            else:
                output_blocks.append(
                    'fi',
                )
        if action_messages.after:
            output_blocks.append(
                self.context.format_blocks(
                    f'echo -e "\\n{self.context.format(action_messages.after)}"',
                )
            )
        return os.linesep.join(output_blocks)

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

    def execute(self, host: str = None, user: str = None) -> CompletedProcess:
        # Parameters may have symbols needing expansion.
        if host:
            host = self.context.format(host)
        if user:
            user = self.context.format(user)

        if not self.blocks:
            self.context.error('Script is empty.')
            return CompletedProcess('', 0)

        with NamedTemporaryFile(mode='w',
                                encoding='utf-8',
                                suffix='.sh',
                                prefix='scripter_',
                                dir='/tmp',
                                delete=not (Options.keep_files or Options.debug),
                                ) as fp:

            host_string = self.format_host_string(host=host, user=user)
            output_label = f'[host={host}] ' if host else ''

            with self.context.sub_context(host=host,
                                          user=user,
                                          host_string=host_string,
                                          tempfile=fp.name,
                                          ) as sub_context:
                # NB: It's important not to re-expand symbols, e.g. by using
                # format...() methods, because the script body may have curly
                # braces that look like symbol markers. We assume all text
                # expansion happened as blocks were added.
                script_text = f'{os.linesep}{os.linesep}'.join([
                    '#!/usr/bin/env bash',
                    f'set -e{"x" if Options.debug else ""}',
                    'echo "::: ${BASH_SOURCE[0]} :::"',
                    self.get_script_body(),
                ])

                # Save the script to a temporary file.
                if Options.debug:
                    sub_context.heading(1, 'Script (begin)')
                    sys.stdout.write(script_text)
                    sys.stdout.write(os.linesep)
                    sub_context.heading(1, 'Script (end)')
                fp.write(f'{script_text}{os.linesep}')
                fp.flush()
                sub_context.message('Temporary script saved: {tempfile}')
                if Options.pause:
                    input('Press Enter to continue:')

                # Execute the temporary script locally or using SSH.
                if host:
                    final_command = sub_context.format('ssh -qt {host_string} bash {tempfile}')
                else:
                    final_command = sub_context.format('/bin/bash {tempfile}')
                if Options.dry_run:
                    run(['cat', fp.name])
                    return CompletedProcess(final_command, 0)
                if host:
                    proc = run(['scp', fp.name, f'{host_string}:{fp.name}'])
                    if proc.returncode != 0:
                        sub_context.abort('Failed to copy script to host.')
                sub_context.message(f'command: {final_command}')

                # Run the script.
                self.context.heading(1, f'{output_label}output (start)')
                proc = run(final_command, shell=True)
                self.context.heading(1, f'{output_label}output (end)')

                if proc.returncode != 0 and not self.unchecked:
                    sub_context.abort('Script execution failed.')
                return proc
