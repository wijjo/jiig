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

"""Filesystem and path manipulation utilities."""

import os
import re
import shutil
import stat
from abc import ABC, abstractmethod
from contextlib import contextmanager, AbstractContextManager
from glob import glob
from pathlib import Path
from typing import Iterator, Any, Sequence

from .thirdparty.gitignore_parser import gitignore_parser

from .collections import make_list
from .log import abort, log_message, log_error, log_heading
from .options import OPTIONS
from .process import run
from .text.blocks import trim_text_blocks
from .text.human_units import format_human_byte_count

# noinspection RegExpRedundantClassElement
REMOTE_PATH_REGEX = re.compile(r'^([\w\d.@-]+):([\w\d_-~/]+)$')
GLOB_CHARACTERS_REGEX = re.compile(r'[*?\[\]]')


def folder_path_string(path: str | Path) -> str:
    """Provide normalized path string, including trailing '/' for a folder.

    Args:
        path: path to normalize

    Returns:
        normalized path string
    """
    path = str(path)
    if not path.endswith('/'):
        path += '/'
    return path


def is_remote_path(path: str | Path) -> bool:
    """Check if path looks like a remote path.

    Args:
        path: path to check

    Returns:
        True if path is remote
    """
    return bool(REMOTE_PATH_REGEX.match(str(path)))


def search_folder_stack_for_file(folder: str | Path,
                                 name: str,
                                 ) -> Path | None:
    """Look up folder stack for a specific file or folder name.

    Name can be a relative path with '/' separators.

    Args:
        folder: starting folder path
        name: file or folder name to look for

    Returns:
        found folder path or None if the name was not found
    """
    if isinstance(folder, str):
        folder = Path(folder)
    check_folder = folder
    while True:
        if (check_folder / name).exists():
            return check_folder
        next_check_folder = check_folder.parent
        if next_check_folder == check_folder:
            return None
        check_folder = next_check_folder


def short_path(long_path: str | Path,
               is_folder: bool = None,
               real_path: bool = False,
               is_local: bool = False,
               ) -> str:
    """Shorten path, e.g. for display.

    Args:
        long_path: path to shorten
        is_folder: consider it a folder if True
        real_path: resolve real path if True
        is_local: assume it is a local path if True

    Returns:
        shortened path
    """
    long_path = str(long_path)
    # Special case for remote paths.
    if not is_local and is_remote_path(long_path):
        if is_folder:
            return folder_path_string(long_path)
        return long_path
    # Normal handling of local paths.
    if real_path:
        path = os.path.realpath(long_path)
    else:
        path = os.path.abspath(long_path)
    if path.endswith(os.path.sep):
        path = path[:-1]
    working_folder = os.getcwd()
    if real_path:
        working_folder = os.path.realpath(working_folder)
    if path.startswith(working_folder + os.path.sep):
        path = path[len(working_folder) + 1:]
    else:
        parent_folder = os.path.dirname(working_folder)
        if path.startswith(parent_folder + os.path.sep):
            path = os.path.join('..', path[len(parent_folder) + 1:])
    if not path:
        path = '.'
    if is_folder or (is_folder is not None and os.path.isdir(path)):
        path = folder_path_string(path)
    return path


def delete_folder(folder_path: str | Path, quiet: bool = False):
    """Delete folder and its contents.

    Args:
        folder_path: folder to delete path
        quiet: suppress non-error messages if True
    """
    folder_path = str(folder_path)
    short_folder_path = short_path(folder_path, is_folder=True)
    if os.path.exists(folder_path):
        if not quiet:
            log_message('Delete folder and contents.', short_folder_path)
        run(['rm', '-rf', short_folder_path])


def delete_file(file_path: str | Path, quiet: bool = False):
    """Delete file.

    Args:
        file_path: file to delete path
        quiet: suppress non-error messages if True
    """
    file_path = str(file_path)
    if os.path.exists(file_path):
        if not quiet:
            log_message('Delete file.', short_path(file_path))
        run(['rm', '-f', file_path], quiet=quiet)


def is_glob_pattern(path: str | Path) -> bool:
    """Check if input path looks like a glob pattern (contains * ? [ ]).

    Args:
        path: input path to check for glob characters

    Returns:
        True if path contains any glob characters
    """
    return GLOB_CHARACTERS_REGEX.search(str(path)) is not None


def create_folder(folder_path: str | Path,
                  delete_existing: bool = False,
                  quiet: bool = False,
                  ):
    """Create folder.

    Args:
        folder_path: folder path
        delete_existing: delete existing folder if True
        quiet: suppress non-error messages if True
    """
    short_folder_path = short_path(folder_path)
    if delete_existing:
        delete_folder(folder_path, quiet=quiet)
    if not os.path.exists(folder_path):
        if not quiet:
            log_message('Create folder.', short_folder_path)
        run(['mkdir', '-p', short_folder_path], quiet=quiet)
    elif not os.path.isdir(folder_path):
        abort('Path is not a folder', short_folder_path)


def check_file_exists(file_path: str | Path):
    """Make sure a file exists.

    Abort if the file is missing.

    Args:
        file_path: path of file to check
    """
    if not os.path.exists(file_path):
        abort('File does not exist.', short_path(file_path))
    if not os.path.isfile(file_path):
        abort('Path is not a file.', short_path(file_path))


def check_folder_exists(folder_path: str | Path):
    """Make sure a folder exists.

    Abort if the folder is missing.

    Args:
        folder_path: path of folder to check
    """
    if not os.path.exists(folder_path):
        abort('Folder does not exist.', short_path(folder_path, is_folder=True))
    if not os.path.isdir(folder_path):
        abort('Path is not a folder.', short_path(folder_path, is_folder=True))


def check_file_not_exists(file_path: str | Path):
    """Make sure a file does not already exist.

    Abort if something exists at that path.

    Args:
        file_path: path of file to check
    """
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            abort('File path already exists as a folder.', short_path(file_path))
        abort('File already exists.', short_path(file_path))


def check_folder_not_exists(folder_path: str | Path):
    """Make sure a folder does not already exist.

    Abort if something exists at that path.

    Args:
        folder_path: path of folder to check
    """
    if os.path.exists(folder_path):
        if not os.path.isdir(folder_path):
            abort('Folder path already exists as a file.', short_path(folder_path))
        abort('Folder already exists.', short_path(folder_path))


def copy_folder(source_folder_path: str | Path,
                target_folder_path: str | Path,
                merge: bool = False,
                quiet: bool = False,
                ):
    """Copy source folder to destination using rsync or cp as appropriate.

    Args:
        source_folder_path: source folder path
        target_folder_path: target folder path
        merge: add files to existing target folder if True
        quiet: suppress non-error messages if True
    """
    if not OPTIONS.dry_run:
        check_folder_exists(source_folder_path)
    if not merge:
        delete_folder(target_folder_path, quiet=quiet)
    create_folder(os.path.dirname(target_folder_path), quiet=quiet)
    short_source_folder_path = short_path(source_folder_path, is_folder=True)
    short_target_folder_path = short_path(target_folder_path, is_folder=True)
    if not quiet:
        log_message('Folder copy.',
                    source=short_source_folder_path,
                    target=short_target_folder_path)
    if os.path.isdir(target_folder_path):
        run(['rsync', '-aq', short_source_folder_path, short_target_folder_path])
    else:
        run(['cp', '-a', short_source_folder_path, short_target_folder_path])


def copy_file(source_file_path: str | Path,
              target_file_path: str | Path,
              overwrite: bool = False,
              quiet: bool = False,
              ):
    """Copy file to fully-specified file path, not a folder.

    Args:
        source_file_path: source file path
        target_file_path: target file path
        overwrite: overwrite existing files if True
        quiet: suppress non-error messages if True
    """
    _copy_or_move_file(source_file_path,
                       target_file_path,
                       move=False,
                       overwrite=overwrite,
                       quiet=quiet)


def copy_files(source_file_pattern: str | Path,
               target_folder_path: str,
               allow_empty: bool = False,
               quiet: bool = False,
               ):
    """Copy files using glob patterns to destination folder.

    Args:
        source_file_pattern: source file glob pattern
        target_folder_path: target folder path
        allow_empty: suppress error for empty source file list if True
        quiet: suppress non-error messages if True
    """
    source_paths = glob(str(source_file_pattern))
    short_target_folder_path = short_path(target_folder_path, is_folder=True)
    if not source_paths and not allow_empty:
        abort('File copy source is empty.', source_file_pattern)
    create_folder(target_folder_path, quiet=quiet)
    if not quiet:
        log_message('File copy.',
                    source=short_path(source_file_pattern),
                    target=short_target_folder_path)
    for source_path in source_paths:
        run(['cp', short_path(source_path), short_target_folder_path])


def move_file(source_file_path: str,
              target_file_path: str,
              overwrite: bool = False,
              quiet: bool = False,
              ):
    """Move a file to a fully-specified file path, not a folder.

    Args:
        source_file_path: source file path
        target_file_path: target file path
        overwrite: overwrite target if True
        quiet: suppress non-error messages if True
    """
    _copy_or_move_file(source_file_path,
                       target_file_path,
                       move=True,
                       overwrite=overwrite,
                       quiet=quiet)


def _copy_or_move_file(src_path: str | Path,
                       dst_path: str | Path,
                       move: bool = False,
                       overwrite: bool = False,
                       quiet: bool = False,
                       ):
    if not OPTIONS.dry_run:
        check_file_exists(src_path)
    if overwrite:
        # If overwriting is allowed a file (only) can be clobbered.
        if os.path.exists(dst_path) and not OPTIONS.dry_run:
            check_file_exists(dst_path)
    else:
        # If overwriting is prohibited don't clobber anything.
        if not OPTIONS.dry_run:
            check_file_not_exists(dst_path)
    parent_folder = os.path.dirname(dst_path)
    if not os.path.exists(parent_folder):
        create_folder(parent_folder, quiet=quiet)
    if move:
        run(['mv', '-f', short_path(src_path), short_path(dst_path)])
    else:
        run(['cp', '-af', short_path(src_path), short_path(dst_path)])


def move_folder(source_folder_path: str | Path,
                target_folder_path: str | Path,
                overwrite: bool = False,
                quiet: bool = False,
                ):
    """Move a folder to a fully-specified folder path, not a parent folder.

    Args:
        source_folder_path: source folder path
        target_folder_path: target folder path
        overwrite: overwrite target if True
        quiet: suppress non-error messages if True
    """
    short_source_folder_path = short_path(source_folder_path, is_folder=True)
    short_target_folder_path = short_path(target_folder_path, is_folder=True)
    if not OPTIONS.dry_run:
        check_folder_exists(source_folder_path)
    if overwrite:
        delete_folder(target_folder_path, quiet=quiet)
    else:
        if not OPTIONS.dry_run:
            check_folder_not_exists(target_folder_path)
    parent_folder_path = os.path.dirname(target_folder_path)
    if not os.path.exists(parent_folder_path):
        create_folder(parent_folder_path, quiet=quiet)
    run(['mv', '-f', short_source_folder_path, short_target_folder_path])


def synchronize_folders(source_folder_path: str | Path,
                        target_folder_path: str | Path,
                        exclude: list = None,
                        check_contents: bool = False,
                        show_files: bool = False,
                        quiet: bool = False,
                        ):
    """Synchronize folders using rsync.

    Args:
        source_folder_path: source folder path
        target_folder_path: target folder path
        exclude: optional exclusions (rsync --exclude options)
        check_contents: compare file contents if True (rsync -c option)
        show_files: display synchronized files (rsync -v option)
        quiet: suppress non-error messages
    """
    # Add the trailing slash for rsync. This works for remote paths too.
    source_folder_path_string = folder_path_string(source_folder_path)
    target_folder_path_string = folder_path_string(target_folder_path)
    if not quiet:
        log_message('Folder sync.',
                    source=source_folder_path_string,
                    target=target_folder_path_string,
                    exclude=exclude or [])
    cmd_args = ['rsync']
    if OPTIONS.dry_run:
        cmd_args.append('--dry-run')
    cmd_args.extend(['-a', '--stats', '-h'])
    if check_contents:
        cmd_args.append('-c')
    if show_files:
        cmd_args.append('-v')
    if exclude:
        for excluded in exclude:
            cmd_args.extend(['--exclude', excluded])
    cmd_args.extend([source_folder_path_string, target_folder_path_string])
    run(cmd_args)


@contextmanager
def temporary_working_folder(folder_path: str | Path | None,
                             quiet: bool = False,
                             ) -> AbstractContextManager[Path]:
    """Change work folder and restore when done.

    Treats an empty or None folder, or when folder is the current work folder, a
    do-nothing operation. But at least the caller doesn't have to check.

    Args:
        folder_path: path of folder to become the working folder
        quiet: suppress non-error messages

    Returns:
        saved working folder path string
    """
    restore_folder_path = Path(os.getcwd())
    if folder_path and os.path.realpath(folder_path) != restore_folder_path:
        log_message('Change working directory.', str(folder_path), debug=quiet)
        os.chdir(folder_path)
    yield restore_folder_path
    if folder_path and os.path.realpath(folder_path) != restore_folder_path:
        log_message('Restore working directory.', str(restore_folder_path), debug=quiet)
        os.chdir(restore_folder_path)


class FileFilter(ABC):
    """Abstract base class for file filters."""
    def __init__(self, source_folder_path: str | Path):
        """File filter constructor.

        Args:
            source_folder_path: source folder path
        """
        if not isinstance(source_folder_path, Path):
            source_folder_path = Path(source_folder_path)
        self.source_folder = source_folder_path

    @abstractmethod
    def accept(self, path: str | Path) -> bool:
        """Required override to accept or reject a path.

        Args:
            path: path to check

        Returns:
            True if the path is accepted
        """
        ...


class ExcludesFilter(FileFilter):
    """File filter supporting .gitignore-style exclusions."""
    def __init__(self,
                 source_folder_path: str | Path,
                 exclusion_patterns: str | Sequence[str] | None,
                 ):
        """ExcludesFilter constructor.

        Args:
            source_folder_path: source folder path
            exclusion_patterns: .gitignore style exclusion pattern(s)
        """
        exclusion_patterns = make_list(exclusion_patterns)
        if exclusion_patterns:
            self.match_function = gitignore_parser.parse_gitignore_patterns(
                exclusion_patterns, source_folder_path)
        else:
            self.match_function = None
        super().__init__(source_folder_path)

    def accept(self, path: str | Path) -> bool:
        """Required override to accept or reject a path.

        Args:
            path: path to check

        Returns:
            True if the path is accepted
        """
        if not self.match_function:
            return True
        return not self.match_function(str(path))


class GitignoreFilter(FileFilter):
    """File filter supporting exclusions declared in ~/.gitignore."""
    def __init__(self, source_folder_path: str | Path):
        """GitignoreFilter constructor.

        Args:
            source_folder_path: source folder path
        """
        super().__init__(source_folder_path)
        gitignore_path = os.path.join(self.source_folder, '.gitignore')
        if os.path.isfile(gitignore_path):
            self.matcher = gitignore_parser.parse_gitignore_file(gitignore_path)
        else:
            self.matcher = None

    def accept(self, path: str | Path) -> bool:
        """Required override to accept or reject a path.

        Args:
            path: path to check

        Returns:
            True if the path is accepted
        """
        if not self.matcher:
            return True
        return not self.matcher(str(path))


def iterate_files(source_folder_path: str | Path,
                  ) -> Iterator[Path]:
    """Files iteration.

    Args:
        source_folder_path: source folder path

    Returns:
        found Path iterator
    """
    source_folder_path_string = str(source_folder_path)
    discard_length = len(source_folder_path_string)
    if not source_folder_path_string.endswith(os.path.sep):
        discard_length += 1
    # Top-down traversal allows preempting descents into rejected folders.
    for dir_path, _sub_dir_paths, file_names in os.walk(source_folder_path, topdown=True):
        relative_dir_name = dir_path[discard_length:]
        for file_name in file_names:
            yield Path(os.path.join(relative_dir_name, file_name))


def iterate_git_pending(source_folder_path: str | Path,
                        ) -> Iterator[Path]:
    """Git pending files iteration.

    Args:
        source_folder_path: source folder path

    Returns:
        found Path iterator
    """
    with temporary_working_folder(source_folder_path, quiet=True):
        git_proc = run(['git', 'status', '-s', '-uno'],
                       capture=True,
                       run_always=True,
                       quiet=True)
        for line in git_proc.stdout.split(os.linesep):
            path = line[3:]
            if os.path.isfile(path):
                yield Path(path)


def iterate_filtered_files(source_folder_path: str | Path,
                           excludes: list[str] = None,
                           gitignore: bool = False,
                           ) -> Iterator[Path]:
    """Filtered files iteration.

    Args:
        source_folder_path: source folder path
        excludes: optional .gitignore exclusion patterns
        gitignore: apply ~/.gitignore exclusions

    Returns:
        found Path iterator
    """
    file_filters: list[FileFilter] = []
    if excludes:
        file_filters.append(ExcludesFilter(source_folder_path, excludes))
    if gitignore:
        file_filters.append(GitignoreFilter(source_folder_path))
    # Discard length supports relative path truncation.
    source_folder_path_string = str(source_folder_path)
    discard_length = len(source_folder_path_string)
    if not source_folder_path_string.endswith(os.path.sep):
        discard_length += 1
    # Top-down traversal allows preempting descents into rejected folders.
    for folder, sub_folders, file_names in os.walk(source_folder_path, topdown=True):
        rel_folder = folder[discard_length:]
        # Remove sub-folders that are rejected by filters.
        to_remove_idxs: list[int] = []
        for idx, sub_folder in enumerate(sub_folders):
            sub_folder_path = Path(os.path.join(rel_folder, sub_folder))
            if any((not file_filter.accept(sub_folder_path) for file_filter in file_filters)):
                to_remove_idxs.append(idx)
        if to_remove_idxs:
            for to_remove_idx in reversed(to_remove_idxs):
                del sub_folders[to_remove_idx]
        # Yield all the files in this folder that pass muster.
        for file_name in file_names:
            path = Path(os.path.join(rel_folder, file_name))
            if all((file_filter.accept(path) for file_filter in file_filters)):
                yield path


def find_system_program(name: str) -> Path | None:
    """Search system PATH for named program.

    Args:
        name: program name

    Returns:
        path if found or None
    """
    for folder in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and (os.stat(path).st_mode & stat.S_IEXEC):
            return Path(path)
    return None


def choose_program_alternative(*programs: Any,
                               required: bool = False,
                               ) -> list[str] | None:
    """Search system PATH for one or more alternative programs, optionally with arguments.

    Args:
        *programs: program name(s) or argument lists/tuples
        required: fatal error if True and program was not found

    Returns:
        first found program as a command argument list
    """
    for program in programs:
        name = program[0] if isinstance(program, (list, tuple)) else str(program)
        if find_system_program(name):
            return [str(arg) for arg in make_list(program)]
    if required:
        abort('Required program not found.', programs=programs)
    return None


def make_relative_path(path: str | Path,
                       start: str | Path = None,
                       ) -> Path:
    """Construct a relative path.

    Mainly a wrapper for os.path.relpath(), but it strips off leading './' to
    provided cleaner paths.

    Args:
        path: path to convert to relative
        start: optional start path

    Returns:
        relative path
    """
    rel_path = os.path.relpath(path, start=start)
    if rel_path == '.':
        return Path(rel_path[1:])
    if rel_path.startswith('./'):
        return Path(rel_path[2:])
    return Path(rel_path)


def change_permissions(path: str | Path,
                       permissions: str,
                       ):
    """Change file or folder permissions.

    Args:
        path: file or folder path
        permissions: chmod-style permission string
    """
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        log_error(f'Target for permissions change is missing: {str(path)}')
        return
    run(['chmod', permissions, str(path)])


def grep(path: str | Path,
         pattern: str,
         case_insensitive: bool = False,
         ) -> Iterator[str]:
    """Search for a regular expression in a file.

    Args:
        path: file path
        pattern: regular expression pattern to compile and search for
        case_insensitive: perform a case-insensitive search

    Returns:
        found line iterator
    """
    if isinstance(path, str):
        path = Path(path)
    else:
        path = path.expanduser()
    if path.exists():
        compile_option_args = [re.IGNORECASE] if case_insensitive else []
        compiled_pattern = re.compile(pattern, *compile_option_args)
        with open(path, encoding='utf-8') as open_file:
            for line in open_file.readlines():
                if compiled_pattern.search(line):
                    yield line


def contains(path: str | Path,
             pattern: str,
             case_insensitive: bool = False,
             ) -> bool:
    """Search for a regular expression in a file and return True if found.

    Args:
        path: file path
        pattern: regular expression pattern to compile and search for
        case_insensitive: perform a case-insensitive search

    Returns:
        True if the pattern was found
    """
    return bool(list(grep(path, pattern, case_insensitive=case_insensitive)))


def add_text(path: str | Path,
             *blocks: str,
             backup: bool = True,
             permissions: str = None,
             exists_pattern: str = None,
             keep_indent: bool = False,
             heading: str = None,
             skip_message: str = None,
             ):
    """Append text block(s) to file as needed.

    Can be gated by checking for a regular expression existence pattern.

    Args:
        path: file path (will be expanded)
        *blocks: text block(s) to expand and append if required
        backup: backup the file if True
        permissions: optional permissions to apply
        exists_pattern: optional regular expression check if missing
        keep_indent: preserve indentation if True
        heading: optional displayed heading
        skip_message: optional message displayed when skipping the file, e.g.
            due to missing text
    """
    if isinstance(path, str):
        path = Path(path)
    else:
        path = path.expanduser()
    if heading:
        log_heading(heading, level=1)
    exists = path.exists()
    if exists_pattern and contains(path, exists_pattern):
        if skip_message:
            log_message(skip_message)
        return
    if backup:
        if exists:
            shutil.copy(path, f'{str(path)}.backup')
    with open(path, 'a', encoding='utf-8') as open_file:
        if exists:
            open_file.write(os.linesep)
        for line in trim_text_blocks(*blocks, keep_indent=keep_indent):
            open_file.write(line)
            open_file.write(os.linesep)
    if permissions is not None:
        change_permissions(path, permissions)


def format_file_size(byte_count: int | None,
                     unit_format: str = None,
                     decimal_places: int = 1,
                     default: str = None
                     ) -> str:
    """
    Format size with support for common size formatting options.

    Note that decimal_units and binary_units should not both be True. If both
    are False the number is converted to text without additional formatting.

    Args:
        byte_count: size as byte count to convert to text
        unit_format: 'd' for KB/MB/..., 'b' for KiB/MiB/..., or bytes if None
        decimal_places: number of decimal places to display
        default: text returned when byte_count is None (default is '-')

    Returns:
        formatted byte count string, with units applied as needed
    """
    if byte_count is None:
        return default or '-'
    return format_human_byte_count(byte_count,
                                   unit_format=unit_format,
                                   decimal_places=decimal_places)
