"""
Context for text expansion and external command execution environment.
"""
import os
import re
import shutil
import subprocess
from getpass import getpass
from typing import List, Union, Sequence, Iterator, Optional, IO, Iterable, Tuple

from . import stream
from .action_messages import ActionMessages
from .context import Context
from .general import trim_text_blocks, plural
from .network import format_host_string
from .options import Options
from .script import Script
from .template_expansion import expand_folder

# Precedes the script body in generated script files.
SCRIPT_PREAMBLE = '''
#!/usr/bin/env bash

set -e%s

echo "::: ${{BASH_SOURCE[0]}} :::"
'''.strip()


class ContextOutputFile(stream.OutputFile):
    """
    Special output file with additional context expansion methods and data.

    Generally not used directly. It is returned by Context.open_output_file().

    Additional data:
    - path: open file path

    Additional methods:
    - write_expanded(): write data to file with symbolic expansion
    - writelines_expanded(): write lines to file with symbolic expansion
    """

    def __init__(self, open_file: IO, context: 'ActionContext', path: Optional[str]):
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


class ActionContext(Context):
    """Nestable execution context with text expansion symbols."""

    def __init__(self, parent: Optional[Context], **kwargs):
        """
        Construct action context.

        :param parent: optional parent context for symbol inheritance
        :param kwargs: initial symbols
        """
        super().__init__(parent, **kwargs)
        self.initial_working_folder = os.getcwd()
        self.working_folder_changed = False

    def __enter__(self) -> 'ActionContext':
        """
        Context management protocol enter method.

        Called at the start when an ActionContext is used in a with block. Saves
        the working directory.

        :return: Context object
        """
        self.initial_working_folder = os.getcwd()
        self.working_folder_changed = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context management protocol exit method.

        Called at the end when an ActionContext is used in a with block.
        Restores the original working directory if it was changed by calling
        working_folder() method.

        :param exc_type: exception type
        :param exc_val: exception value
        :param exc_tb: exception traceback
        :return: True to suppress an exception that occurred in the with block
        """
        if self.working_folder_changed:
            os.chdir(self.initial_working_folder)
            self.working_folder_changed = False
        return False

    def working_folder(self, folder: str) -> str:
        """
        Change the working folder.

        Original working folder is restored by the contextmanager wrapped around
        the sub_context creation.

        :param folder: new working folder
        :return: previous working folder
        """
        os.chdir(folder)
        self.working_folder_changed = True
        return os.getcwd()

    def run_command(self,
                    command: Union[str, Sequence],
                    predicate: str = None,
                    capture: bool = False,
                    unchecked: bool = False,
                    ignore_dry_run: bool = False,
                    messages: dict = None,
                    working_folder: str = None,
                    **subprocess_run_kwargs,
                    ) -> subprocess.CompletedProcess:
        """
        Run a command with support for predicate, messages, and dry-run.

        :param command: command as string or argument list
        :param predicate: optional predicate condition to apply
        :param capture: capture output if True
        :param unchecked: do not check for failure
        :param ignore_dry_run: execute even if it is a dry run
        :param messages: messages to add to output
        :param working_folder: temporary working folder for command execution
        :param subprocess_run_kwargs: additional subprocess.run() keyword arguments
        :return: subprocess run() result
        """
        with ActionContext(self, command=command, predicate=predicate) as context:

            action_messages = ActionMessages.from_dict(messages)

            if action_messages.before:
                context.heading(1, action_messages.before)

            context.message('command: {command}')
            if predicate:
                context.message('predicate: {predicate}')

            if Options.dry_run and not ignore_dry_run:
                return subprocess.CompletedProcess(command, 0)

            if predicate is not None:
                predicate_proc = context.run_subprocess('{predicate}', shell=True)
                if predicate_proc.returncode != 0:
                    if action_messages.skip:
                        context.message(action_messages.skip)
                return subprocess.CompletedProcess(command, 0)

            if 'shell' not in subprocess_run_kwargs:
                subprocess_run_kwargs['shell'] = True
            if capture:
                subprocess_run_kwargs.update(capture_output=True, encoding='utf-8')

            if working_folder:
                context.working_folder(working_folder)

            proc = context.run_subprocess('{command}', **subprocess_run_kwargs)

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

    def open_input_file(self, path: str, binary: bool = False) -> IO:
        """
        Convenient layer over open() with better defaults and symbol expansion.

        Provides an IO-compatible object, usable in a `with` statement, that
        performs symbolic text expansion.

        :param path: file path, possibly including a '?' marker to create a temporary file
        :param binary: open the file in binary mode (defaults to utf-8 text)
        :return: open file object, usable in a `with` statement for automatic closing
        """
        return stream.open_input_file(self.format(path), binary=binary)

    def open_output_file(self,
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
        with Context(self, path=path) as context:
            opened_file_data = stream.open_output_file(context.symbols.path,
                                                       binary=binary,
                                                       keep_temporary=keep_temporary,
                                                       create_parent_folder=True)
            return ContextOutputFile(opened_file_data.open_file, self, opened_file_data.path)

    # noinspection PyShadowingBuiltins
    def run_subprocess(self,
                       command_or_commands: Union[str, Sequence[str]],
                       **subprocess_run_kwargs,
                       ) -> subprocess.CompletedProcess:
        """
        Context-based front end to subprocess.run() with text expansion.

        :param command_or_commands: command string or sequence
        :param subprocess_run_kwargs: additional keyword arguments to subprocess.run()
        :return: subprocess.run() CompletedProcess return value
        """
        if isinstance(command_or_commands, (list, tuple)):
            return subprocess.run([self.format(arg) for arg in command_or_commands],
                                  **subprocess_run_kwargs)
        return subprocess.run(self.format(command_or_commands),
                              **subprocess_run_kwargs)

    def _get_host_user(self,
                       host: Optional[str],
                       user: Optional[str],
                       host_string: Optional[str],
                       ) -> Tuple[str, str]:
        if host_string:
            user_host = host_string.split('@', maxsplit=1)
            if len(user_host) == 2:
                return user_host[1], user_host[0]
            self.error(f'Bad host_string value: {host_string}')
        return host, user

    def run_script(self,
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
        :param messages: optional display messages
        :param unchecked: do not check return code for success
        :param ignore_dry_run: execute even if it is a dry run
        :return: subprocess.CompletedProcess result
        """
        dry_run = Options.dry_run and not ignore_dry_run

        host, user = self._get_host_user(host, user, host_string)

        if host:
            command = 'ssh -qt {target_host_string} bash {script_file}'
            deploy_command = 'scp {script_file} {target_host_string}:{script_file}'
        else:
            command = '/bin/bash {script_file}'
            deploy_command = None

        # Outer context has immediately-resolvable symbols, e.g. expanded for file output.
        with ActionContext(self,
                           target_host=host,
                           target_user=user,
                           target_host_string=format_host_string(host=host, user=user),
                           script_preamble=_get_script_preamble(),
                           script_body=_get_script_body(script_text_or_object),
                           output_label='[host={target_host}] ' if host else ''
                           ) as script_context:

            # The stream from self.open_output_file() automatically expands text symbols.
            with script_context.open_output_file(script_path or '/tmp/scripter_?.sh') as output_file:

                # Inner context symbols needed the script file path to resolve.
                with ActionContext(script_context,
                                   script_file=output_file.path,
                                   command=command,
                                   deploy_command=deploy_command,
                                   ) as run_context:

                    run_context._script_execution_start(messages)

                    if Options.debug or dry_run:
                        run_context.heading(1, 'Script {script_file} (begin)')
                        run_context.message('{script_preamble}{nl}{nl}{script_body}')
                        run_context.heading(1, 'Script {script_file} (end)')

                    # Write script file.
                    output_file.write_expanded('{script_preamble}{nl}{nl}{script_body}')
                    output_file.flush()
                    run_context.message('Script saved: {script_file}')
                    if Options.pause:
                        input('Press Enter to continue:')

                    if dry_run:
                        return subprocess.CompletedProcess(command, 0)

                    # Deploy the script?
                    if deploy_command:
                        proc = run_context.run_subprocess('{deploy_command}', shell=True)
                        if proc.returncode != 0:
                            run_context.abort('Failed to deploy script.')

                    # Run the script.
                    run_context.message('command: {command}')
                    run_context.heading(1, '{output_label}output (start)')
                    proc = run_context.run_subprocess('{command}', shell=True)
                    run_context.heading(1, '{output_label}output (end)')

                    # Display final messages and handle failure.
                    return run_context._script_execution_finish(proc, messages, unchecked)

    def run_script_code(self,
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
        :param messages: optional display messages
        :param unchecked: do not check return code for success
        :param ignore_dry_run: execute even if it is a dry run
        :return: subprocess.CompletedProcess result
        """
        dry_run = Options.dry_run and not ignore_dry_run

        host, user = self._get_host_user(host, user, host_string)

        if host:
            command = 'ssh -qt {host_string} bash -c "\'{script_body}\'"'
            quoted = True
        else:
            command = 'bash -c "{script_body}"'
            quoted = False

        with ActionContext(self,
                           host=host,
                           user=user,
                           host_string=format_host_string(host=host, user=user),
                           script_body=_get_script_body(script_text_or_object, quoted=quoted),
                           command=command,
                           output_label='[host={host}] ' if host else ''
                           ) as sub_context:

            sub_context._script_execution_start(messages)

            if Options.debug or dry_run:
                sub_context.heading(1, 'Script code (begin)')
                sub_context.message('{script_body}')
                sub_context.heading(1, 'Script code (end)')

            if dry_run:
                return subprocess.CompletedProcess(command, 0)

            if Options.pause:
                input('Press Enter to continue:')

            sub_context.message('command: {command}')

            # Run the script.
            sub_context.heading(1, '{output_label}output (start)')
            proc = sub_context.run_subprocess('{command}', shell=True)
            sub_context.heading(1, '{output_label}output (end)')

            return sub_context._script_execution_finish(proc, messages, unchecked)

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
        with Context(self, paths=paths) as context:
            missing = [path for path in context.symbols.paths if not os.path.exists(path)]
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

    def input_password(self, prompt: str = None) -> Optional[str]:
        """
        Input user password.

        :param prompt: optional prompt (default provided by getpass.getpass())
        :return: password
        """
        with ActionContext(self, prompt=prompt) as input_context:
            return getpass(prompt=input_context.symbols.prompt)

    def expand_template_folder(self,
                               source_root: str,
                               target_root: str,
                               sub_folder: str = None,
                               includes: Sequence[str] = None,
                               excludes: Sequence[str] = None,
                               overwrite: bool = False,
                               symbols: dict = None,
                               add_context_symbols: bool = False,
                               ):
        """
        Expand source template folder or sub-folder to target folder.

        Reads source template configuration, if found to determine what kind of
        special handling may be needed.

        :param source_root: template source root folder path
        :param target_root: base target folder
        :param sub_folder: optional relative sub-folder path applied to source and target roots
        :param includes: optional relative paths, supporting wildcards, for files to include
        :param excludes: optional relative paths, supporting wildcards, for files to exclude
        :param overwrite: force overwriting of existing files if True
        :param symbols: symbols used for template expansion
        :param add_context_symbols: add context symbols to template expansion symbols if True
        """
        with ActionContext(self,
                           source_root=source_root,
                           target_root=target_root,
                           sub_folder=sub_folder,
                           includes=includes,
                           excludes=excludes) as context:
            expansion_symbols = {}
            if add_context_symbols:
                expansion_symbols.update(self.symbols)
            if symbols:
                expansion_symbols.update(symbols)
            expand_folder(source_root,
                          target_root,
                          sub_folder=context.symbols.sub_folder,
                          includes=context.symbols.includes,
                          excludes=context.symbols.excludes,
                          overwrite=overwrite,
                          symbols=expansion_symbols,
                          )

    def _script_execution_start(self, messages: Optional[dict]):
        action_messages = ActionMessages.from_dict(messages)
        if action_messages.before:
            self.message(action_messages.before)

    def _script_execution_finish(self,
                                 proc: subprocess.CompletedProcess,
                                 messages: Optional[dict],
                                 unchecked: bool,
                                 ) -> subprocess.CompletedProcess:
        action_messages = ActionMessages.from_dict(messages)
        if proc.returncode == 0:
            if action_messages.success:
                self.message(action_messages.success)
        else:
            if action_messages.failure:
                self.message(action_messages.failure)
            if not unchecked:
                self.abort('Script execution failed.')
        return proc


def _get_script_preamble():
    return SCRIPT_PREAMBLE % ('x' if Options.debug else '')


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
