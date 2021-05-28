#!/usr/bin/env python3

import os
import re
import shutil
from contextlib import contextmanager
from subprocess import run, CompletedProcess
from typing import Iterator, Sequence, Union, ContextManager

from .messages import Messages
from .scripter_base import ScripterBase
from .script import Script
from .utility import repo_name_from_url, trim_text_blocks


class Scripter(ScripterBase):

    def __init__(self, debug: bool = False, dry_run: bool = False, pause: bool = False, **kwargs):
        """
        Construct scripter.

        :param debug: enable debug output
        :param dry_run: do not execute destructive commands
        :param pause: pause before executing scripts
        :param kwargs: keyword argument symbols
        """
        super().__init__(debug=debug, dry_run=dry_run, pause=pause, **kwargs)

    def remote_command(self,
                       host: str,
                       command_string_or_sequence: Union[str, Sequence],
                       user: str = None,
                       predicate: str = None,
                       unchecked: bool = False,
                       messages: Messages = None,
                       ) -> CompletedProcess:
        script_text = self.format_script(command_string_or_sequence,
                                         predicate=predicate,
                                         messages=messages)
        escaped_script_text = script_text.replace("'", "\\'")
        with self.sub_scripter(host_string=f'{user}@{host}' if user else host,
                               escaped_script_text=escaped_script_text,
                               ) as sub_scripter:
            sub_scripter.update(
                ssh_command='''ssh -qt {host_string} bash -c "'{nl}{escaped_script_text}{nl}'"''')
            sub_scripter.message('command: {ssh_command}')
            if self.dry_run:
                proc = CompletedProcess([sub_scripter.get('ssh_command')], 0)
            else:
                proc = run(sub_scripter.get('ssh_command'), shell=True)
                if proc.returncode != 0 and not unchecked:
                    sub_scripter.abort('Remote command failed.')
            return proc

    @contextmanager
    def start_script(self,
                     heading: str = None,
                     unchecked: bool = False,
                     run_as_root: bool = False,
                     script_class: type = None,
                     ) -> ContextManager[Script]:
        if script_class is None:
            script_class = Script
        if heading:
            self.heading(heading)
        script = script_class(dry_run=self.dry_run,
                              debug=self.debug,
                              pause=self.pause,
                              unchecked=unchecked,
                              need_sudo=not run_as_root)
        if self.context.symbols:
            script.copy_symbols(**self.context.symbols)
        yield script

    def get_ip_address(self, host: str) -> str:
        if self.dry_run:
            return '1.1.1.1'
        ip_extract_re = re.compile(rf'^PING {host} \((\d+\.\d+\.\d+\.\d+)\):')
        for line in self.pipe_lines(f'ping -c 1 {host}'):
            result = ip_extract_re.search(line)
            if result:
                return result.group(1)
        self.context.abort(f'Failed to get IP address for host name "{host}".')

    def get_repo_name(self) -> str:
        return repo_name_from_url(self.pipe('git config --get remote.origin.url'))

    @contextmanager
    def chdir(self, folder: str) -> ContextManager[str]:
        orig_dir = os.getcwd()
        os.chdir(folder)
        yield orig_dir
        os.chdir(orig_dir)

    def grep(self, raw_path: str, raw_pattern: str, case_insensitive: bool = False) -> Iterator[str]:
        path = self.context.format(raw_path)
        pattern = self.context.format(raw_pattern)
        if os.path.exists(path):
            compile_option_args = [re.IGNORECASE] if case_insensitive else []
            compiled_pattern = re.compile(pattern, *compile_option_args)
            with open(os.path.expanduser(path), encoding='utf-8') as open_file:
                for line in open_file.readlines():
                    if compiled_pattern.search(line):
                        yield line

    def file_contains(self, raw_path: str, raw_pattern: str, case_insensitive: bool = False) -> bool:
        return bool(list(self.grep(raw_path, raw_pattern, case_insensitive=case_insensitive)))

    def check_file_exists(self, *paths: str):
        missing = [path for path in paths if not os.path.exists(path)]
        if missing:
            self.abort(f'Required file(s) are missing: {" ".join(missing)}')

    def add_text(self,
                 raw_path: str,
                 *blocks: str,
                 backup: bool = True,
                 permissions: str = None,
                 exists_pattern: str = None,
                 messages: Messages = None,
                 keep_indent: bool = False):

        with self.sub_scripter(path=raw_path) as sub_scripter:

            if permissions:
                sub_scripter.copy_symbols(permissions=permissions)
            path = sub_scripter.get('path')

            if messages and messages.heading:
                sub_scripter.heading(messages.heading)

            exists = os.path.exists(path)
            if exists_pattern and self.file_contains(path, exists_pattern):
                if messages and messages.skip:
                    sub_scripter.message(messages.skip)
                return

            if backup:
                path = sub_scripter.format(raw_path)
                if os.path.exists(path):
                    backup_path = sub_scripter.format('{path}.backup')
                    shutil.copy(path, backup_path)

            with open(path, 'a', encoding='utf-8') as open_file:
                if exists:
                    open_file.write(os.linesep)
                for raw_line in trim_text_blocks(*blocks, keep_indent=keep_indent):
                    line = sub_scripter.format(raw_line)
                    open_file.write(line)
                    open_file.write(os.linesep)

            if permissions is not None:
                sub_scripter.run('chmod {permissions} {path}')

    def test_ssh_key(self, host: str, user: str, messages: Messages = None) -> bool:
        with self.sub_scripter(host=host, user=user) as sub_scripter:
            proc = sub_scripter.run(
                'ssh -o PasswordAuthentication=no {user}@{host} true 2> /dev/null',
                ignore_dry_run=True,
                unchecked=True,
                messages=messages,
            )
            return proc.returncode == 0
