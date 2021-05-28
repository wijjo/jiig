"""
Scripter script.
"""

import os
from contextlib import contextmanager
from subprocess import CompletedProcess, run
from tempfile import NamedTemporaryFile
from typing import List, ContextManager, Union, Sequence, Optional

from .messages import Messages
from .scripter_base import ScripterBase
from .utility import trim_text_block


class Script:
    """Used by Runner to build a script piecemeal and then execute it."""

    def __init__(self,
                 debug: bool = False,
                 dry_run: bool = False,
                 pause: bool = False,
                 unchecked: bool = False,
                 need_sudo: bool = False,
                 blocks: List[str] = None,
                 ):
        """
        Construct script.

        :param debug: enable debug output if True
        :param dry_run: do not executed destructive commands if True
        :param pause: pause before script execution if True
        :param unchecked: do not check return code if True
        :param need_sudo: commands need sudo privilege escalation if True
        :param blocks: initial script blocks (not typically used)
        """
        self.unchecked = unchecked
        self.need_sudo = need_sudo
        self.blocks: List[str] = blocks if blocks is not None else []
        self.scripter = ScripterBase(debug=debug, dry_run=dry_run, pause=pause)
        self.scripter.copy_symbols(sudo_preamble='sudo ' if need_sudo else '')

    @property
    def debug(self) -> bool:
        return self.scripter.debug

    @property
    def dry_run(self) -> bool:
        return self.scripter.dry_run

    @property
    def pause(self) -> bool:
        return self.scripter.pause

    def update(self, **kwargs):
        self.scripter.update(**kwargs)

    def copy_symbols(self, **kwargs):
        self.scripter.copy_symbols(**kwargs)

    @contextmanager
    def sub_script(self, **kwargs) -> ContextManager['Script']:
        sub_script = self.__class__(dry_run=self.dry_run,
                                    debug=self.debug,
                                    pause=self.pause,
                                    unchecked=self.unchecked,
                                    need_sudo=self.need_sudo,
                                    blocks=self.blocks)
        # Runner context symbols get copied without expansion.
        if self.scripter.context.symbols:
            sub_script.scripter.copy_symbols(**self.scripter.context.symbols)
        # Keyword argument symbols are expanded using symbols copied from scripter context.
        if kwargs:
            sub_script.scripter.update(**kwargs)
        yield sub_script

    def add_block(self,
                  command_string_or_sequence: Union[str, Sequence],
                  location: str = None,
                  predicate: str = None,
                  messages: Messages = None,
                  ):
        self.blocks.append(
            self.scripter.format_script(
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
               messages: Messages = None,
               ):
        self.blocks.append(
            self.scripter.format_script(
                command,
                predicate=predicate,
                location=location,
                messages=messages,
            )
        )

    def symlink(self, source: str, target: str, messages: Messages = None):
        with self.sub_script(source=source, target=target) as sub_script:
            sub_script.add_block(
                '''
                ln -s {source} {target}
                ''',
                predicate='[[ ! -e {target} ]]',
                messages=messages,
            )

    def apt_install(self,
                    executable: str,
                    *packages: str,
                    messages: Messages = None,
                    ):
        with self.sub_script(executable=executable,
                             packages=' '.join(packages),
                             primary_package=packages[0],
                             ) as sub_script:
            sub_script.add_block(
                '{sudo_preamble}apt install -y {packages}',
                predicate='! command -v {executable} > /dev/null',
                messages=messages,
            )

    @contextmanager
    def chdir(self, folder: str, messages: Messages = None) -> ContextManager[None]:
        with self.sub_script(folder=folder) as sub_script:
            sub_script.add_block('pushd {folder} > /dev/null', messages=messages)
            yield
            sub_script.add_block('popd > /dev/null')

    def create_user(self, user: str, *groups: str, messages: Messages = None):
        with self.sub_script(user=user) as sub_script:
            sub_script.add_block(
                [
                    '{sudo_preamble}adduser {user}'
                ] + [
                    '{sudo_preamble}usermod -aG %s {user}' % group
                    for group in groups
                ],
                predicate='! grep -q ^{user}: /etc/passwd',
                messages=messages,
            )

    def create_folder(self, folder: str, need_root: bool = False, messages: Messages = None):
        with self.sub_script(
            folder=folder,
            sudo_preamble=self.scripter.get('sudo_preamble') if need_root else '',
        ) as sub_script:
            sub_script.add_block(
                '{sudo_preamble}mkdir -p {folder}',
                predicate='[[ ! -d {folder} ]]',
                messages=messages,
            )

    def delete_folder(self, folder: str, need_root: bool = False, messages: Messages = None):
        with self.sub_script(
            folder=folder,
            sudo_preamble=self.scripter.get('sudo_preamble') if need_root else '',
            redirect=' 2> /dev/null' if not self.debug else '',
        ) as sub_script:
            sub_script.add_block(
                '{sudo_preamble}rm -rf {folder}{redirect}',
                predicate='[[ -d {folder} ]]',
                messages=messages,
            )

    def change_shell(self, user: str, shell: str, messages: Messages = None):
        with self.sub_script(user=user, shell=shell) as sub_script:
            sub_script.add_block(
                '{sudo_preamble}chsh -s {shell} {user}',
                predicate='[[ $SHELL != {shell} ]]',
                messages=messages,
            )

    def format_host_string(self, host: str = None, user: str = None) -> Optional[str]:
        if not host:
            return None
        if not user:
            if self.need_sudo:
                return f'root@{host}'
            return host
        return f'{user}@{host}' if user else host

    def execute(self, host: str = None, user: str = None) -> CompletedProcess:
        if not self.blocks:
            self.scripter.error('Script is empty.')
            return CompletedProcess('', 0)

        with NamedTemporaryFile(mode='w',
                                encoding='utf-8',
                                suffix='.sh',
                                prefix='scripter',
                                dir='/tmp',
                                delete=not self.debug,
                                ) as fp:

            with self.scripter.sub_scripter(host=host,
                                            user=user,
                                            host_string=self.format_host_string(host=host, user=user),
                                            tempfile=fp.name,
                                            ) as sub_scripter:
                # NB: It's important not to re-expand symbols, e.g. by using
                # format...() methods, because the script body may have curly
                # braces that look like symbol markers. We assume all text
                # expansion happened as blocks were added.
                script_text = f'{os.linesep}{os.linesep}'.join([
                    '#!/usr/bin/env bash',
                    f'set -e{"x" if self.debug else ""}',
                ] + self.blocks)

                # Clear out the blocks to be able to build the next script.
                self.blocks = []

                # Save the script to a temporary file.
                if self.debug:
                    sub_scripter.heading('Script (begin)')
                    sub_scripter.message(script_text)
                    sub_scripter.heading('Script (end)')
                fp.write(f'{script_text}{os.linesep}')
                fp.flush()
                sub_scripter.message('Temporary script saved: {tempfile}')
                if self.pause:
                    input('Press Enter to continue:')

                # Execute the temporary script locally or using SSH.
                if host:
                    final_command = sub_scripter.format('ssh -qt {host_string} bash {tempfile}')
                else:
                    final_command = sub_scripter.format('/bin/bash {tempfile}')
                if self.dry_run:
                    run(['cat', fp.name])
                    return CompletedProcess(final_command, 0)
                if host:
                    sub_scripter.run('scp {tempfile} {host_string}:{tempfile}')
                sub_scripter.message(f'command: {final_command}')
                proc = run(final_command, shell=True)
                if proc.returncode != 0 and not self.unchecked:
                    sub_scripter.abort(f'Script execution failed.')
                return proc
