"""
Context for text expansion and external command execution environment.
"""

import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from typing import List, Union, ContextManager, TypeVar, Sequence, Iterator

from .action_messages import ActionMessages
from .context import Context
from .general import trim_text_blocks
from .script import Script

T_action_context = TypeVar('T_action_context', bound='ActionContext')
T_script = TypeVar('T_script', bound=Script)


class ActionContext(Context):
    """Nestable execution context with text expansion symbols."""

    def __init__(self):
        """Construct action context."""
        super().__init__()
        self.working_folder_changed = False

    @contextmanager
    def script(self,
               messages: dict = None,
               unchecked: bool = False,
               run_by_root: bool = False,
               script_class: T_script = None,
               ) -> ContextManager[T_script]:
        action_messages = ActionMessages.from_dict(messages)
        if script_class is None:
            script_class = Script
        if action_messages.before:
            self.heading(1, action_messages.before)
        script = script_class(self, unchecked=unchecked, run_by_root=run_by_root)
        if self.symbols:
            script.copy_symbols(**self.symbols)
        yield script
        if action_messages.after:
            self.message(action_messages.after)

    def working_folder(self, folder: str) -> str:
        """
        Change the working folder.

        Original working folder is restored by the contextmanager wrapped around
        the sub_context creation.

        :param folder: new working folder
        :return: previous working folder
        """
        previous_working_folder = os.getcwd()
        os.chdir(folder)
        self.working_folder_changed = True
        return previous_working_folder

    def run_command(self,
                    command: Union[str, Sequence],
                    predicate: str = None,
                    capture: bool = False,
                    unchecked: bool = False,
                    dry_run: bool = False,
                    messages: dict = None,
                    ) -> subprocess.CompletedProcess:
        """
        Run a command.

        :param command: command as string or argument list
        :param predicate: optional predicate condition to apply
        :param capture: capture output if True
        :param unchecked: do not check for failure
        :param dry_run: avoid execution if True
        :param messages: messages to add to output
        :return: subprocess run() result
        """
        action_messages = ActionMessages.from_dict(messages)
        expanded_command = self.format(command)
        expanded_predicate = self.format(predicate)

        if action_messages.before:
            self.heading(1, action_messages.before)

        self.message(f'command: {expanded_command}')
        if expanded_predicate:
            self.message('predicate: {expanded_predicate}')

        if dry_run:
            return subprocess.CompletedProcess([expanded_command], 0)

        if predicate is not None:
            predicate_proc = subprocess.run(expanded_predicate, shell=True)
            if predicate_proc.returncode != 0:
                if action_messages.skip:
                    self.message(action_messages.skip)
            return subprocess.CompletedProcess([expanded_command], 0)

        run_kwargs = dict(shell=True)
        if capture:
            run_kwargs.update(capture_output=True, encoding='utf-8')

        proc = subprocess.run(expanded_command, **run_kwargs)

        if proc.returncode == 0:
            if action_messages.success:
                self.message(action_messages.success)
        else:
            if action_messages.failure:
                self.message(action_messages.failure)
            if not unchecked:
                self.abort('Command failed.')

        if action_messages.after:
            self.message(action_messages.after)

        return proc

    def pipe(self, raw_command: Union[str, List]) -> str:
        """
        Run command and capture output.

        :param raw_command: command to expand and run
        :return: command output block
        """
        proc = self.run_command(raw_command, capture=True)
        return proc.stdout.strip()

    def pipe_lines(self, raw_command: Union[str, List]) -> List[str]:
        """
        Run command and capture output as a list of lines.

        :param raw_command: command to expand and run
        :return: command output lines
        """
        return self.pipe(raw_command).split(os.linesep)

    def grep(self, path: str, raw_pattern: str, case_insensitive: bool = False) -> Iterator[str]:
        """
        Search for a regular expression in a file.

        :param path: file path
        :param raw_pattern: regular expression pattern to expand, compile, search for
        :param case_insensitive: perform a case-insensitive search
        :return: found line iterator
        """
        expanded_path = self.format(path)
        pattern = self.format(raw_pattern)
        if os.path.exists(expanded_path):
            compile_option_args = [re.IGNORECASE] if case_insensitive else []
            compiled_pattern = re.compile(pattern, *compile_option_args)
            with open(os.path.expanduser(expanded_path), encoding='utf-8') as open_file:
                for line in open_file.readlines():
                    if compiled_pattern.search(line):
                        yield line

    def file_contains(self, path: str, raw_pattern: str, case_insensitive: bool = False) -> bool:
        """
        Search for a regular expression in a file and return True if found.

        :param path: file path
        :param raw_pattern: regular expression pattern to expand, compile, search for
        :param case_insensitive: perform a case-insensitive search
        :return: True if the pattern was found
        """
        return bool(list(self.grep(path, raw_pattern, case_insensitive=case_insensitive)))

    def check_file_exists(self, *paths: str):
        """
        Check that one or more files exist and abort if anything is missing.

        :param paths: file paths to check
        """
        missing = [path for path in paths if not os.path.exists(path)]
        if missing:
            self.abort(f'Required file(s) are missing: {" ".join(missing)}')

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
        :param messages: messages to inject into output
        :param keep_indent: preserve indentation if True
        """
        action_messages = ActionMessages.from_dict(messages)
        expanded_path = self.format(path)
        if action_messages.before:
            self.heading(1, action_messages.before)
        exists = os.path.exists(expanded_path)
        if exists_pattern and self.file_contains(expanded_path, exists_pattern):
            if action_messages.skip:
                self.message(action_messages.skip)
            return
        if backup:
            if os.path.exists(expanded_path):
                shutil.copy(path, f'{expanded_path}.backup')
        with open(path, 'a', encoding='utf-8') as open_file:
            if exists:
                open_file.write(os.linesep)
            for raw_line in trim_text_blocks(*blocks, keep_indent=keep_indent):
                line = self.format(raw_line)
                open_file.write(line)
                open_file.write(os.linesep)
        if permissions is not None:
            self.run_command(f'chmod {permissions} {expanded_path}')
        if action_messages.after:
            self.message(action_messages.after)
