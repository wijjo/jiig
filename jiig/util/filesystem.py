"""Path manipulation utilities."""

import os
import re
import stat
from contextlib import contextmanager
from glob import glob
from typing import Text, List, Optional, Iterator, Any

from thirdparty.gitignore_parser import gitignore_parser

from .log import abort, log_message
from .general import make_list
from .options import OPTIONS
from .process import run

REMOTE_PATH_REGEX = re.compile(r'^([\w\d.@-]+):([\w\d_-~/]+)$')
GLOB_CHARACTERS_REGEX = re.compile(r'[*?\[\]]')


def folder_path(path):
    if not path.endswith('/'):
        path += '/'
    return path


def is_remote_path(path: Text) -> bool:
    return bool(REMOTE_PATH_REGEX.match(path))


def search_folder_stack_for_file(folder: Text, name: Text) -> Optional[Text]:
    """
    Look up folder stack for a specific file or folder name.

    :param folder: starting folder path
    :param name: file or folder name to look for
    :return: found folder path or None if the name was not found
    """
    check_folder = folder
    while True:
        if os.path.exists(os.path.join(check_folder, name)):
            return check_folder
        if check_folder in ['', os.path.sep]:
            return None
        check_folder = os.path.dirname(check_folder)


def short_path(path, is_folder=None, real_path=False, is_local=False):
    # Special case for remote paths.
    if not is_local and is_remote_path(path):
        if is_folder:
            return folder_path(path)
        return path
    # Normal handling of local paths.
    path = os.path.realpath(path) if real_path else os.path.abspath(path)
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
        path = folder_path(path)
    return path


def delete_folder(path: Text, quiet: bool = False):
    path = short_path(path, is_folder=True)
    if os.path.exists(path):
        if not quiet:
            log_message('Delete folder and contents.', path)
        run(['rm', '-rf', path])


def delete_file(path: Text, quiet: bool = False):
    path = short_path(path)
    if os.path.exists(path):
        if not quiet:
            log_message('Delete file.', path)
        run(['rm', '-f', path])


def is_glob_pattern(path: Text) -> bool:
    """
    Check if input path looks like a glob pattern (contains * ? [ ]).

    :param path: input path to check for glob characters
    :return: True if path contains any glob characters
    """
    return GLOB_CHARACTERS_REGEX.search(path) is not None


def create_folder(path: Text, delete_existing: bool = False, quiet: bool = False):
    path = short_path(path, is_folder=True)
    if delete_existing:
        delete_folder(path, quiet=quiet)
    if not os.path.exists(path):
        if not quiet:
            log_message('Create folder.', folder_path(path))
        run(['mkdir', '-p', path], quiet=quiet)
    elif not os.path.isdir(path):
        abort('Path is not a folder', path)


def check_file_exists(path: Text):
    if not os.path.exists(path):
        abort('File does not exist.', path)
    if not os.path.isfile(path):
        abort('Path is not a file.', path)


def check_folder_exists(path: Text):
    if not os.path.exists(path):
        abort('Folder does not exist.', path)
    if not os.path.isdir(path):
        abort('Path is not a folder.', path)


def check_file_not_exists(path: Text):
    if os.path.exists(path):
        if os.path.isdir(path):
            abort('File path already exists as a folder.', path)
        abort('File already exists.', path)


def check_folder_not_exists(path: Text):
    if os.path.exists(path):
        if not os.path.isdir(path):
            abort('Folder path already exists as a file.', path)
        abort('Folder already exists.', path)


def copy_folder(src_path: Text,
                dst_path: Text,
                merge: bool = False,
                quiet: bool = False):
    src_folder_path = short_path(src_path, is_folder=True)
    dst_folder_path = short_path(dst_path, is_folder=True)
    if not OPTIONS.dry_run:
        check_folder_exists(src_folder_path)
    if not merge:
        delete_folder(dst_path, quiet=quiet)
    create_folder(os.path.dirname(dst_path), quiet=quiet)
    if not quiet:
        log_message('Folder copy.',
                    source=folder_path(src_folder_path),
                    target=folder_path(dst_folder_path))
    if os.path.isdir(dst_folder_path):
        run(['rsync', '-aq', src_folder_path, dst_folder_path])
    else:
        run(['cp', '-a', src_folder_path, dst_folder_path])


def copy_file(src_path: Text,
              dst_path: Text,
              overwrite: bool = False,
              quiet: bool = False):
    """Copy a file to a fully-specified file path, not a folder."""
    _copy_or_move_file(src_path, dst_path, move=False, overwrite=overwrite, quiet=quiet)


def copy_files(src_glob: Text,
               dst_path: Text,
               allow_empty: bool = False,
               quiet: bool = False):
    src_paths = glob(src_glob)
    if not src_paths and not allow_empty:
        abort('File copy source is empty.', src_glob)
    create_folder(dst_path, quiet=quiet)
    if not quiet:
        log_message('File copy.',
                    source=short_path(src_glob),
                    target=short_path(dst_path, is_folder=True))
    for src_path in src_paths:
        run(['cp', short_path(src_path), short_path(dst_path, is_folder=True)])


def move_file(src_path: Text,
              dst_path: Text,
              overwrite: bool = False,
              quiet: bool = False):
    """Move a file to a fully-specified file path, not a folder."""
    _copy_or_move_file(src_path, dst_path, move=True, overwrite=overwrite, quiet=quiet)


def _copy_or_move_file(src_path: Text,
                       dst_path: Text,
                       move: bool = False,
                       overwrite: bool = False,
                       quiet: bool = False):
    src_path_short = short_path(src_path, is_folder=False)
    dst_path_short = short_path(dst_path, is_folder=False)
    if not OPTIONS.dry_run:
        check_file_exists(src_path_short)
    if overwrite:
        # If overwriting is allowed a file (only) can be clobbered.
        if os.path.exists(dst_path) and not OPTIONS.dry_run:
            check_file_exists(dst_path)
    else:
        # If overwriting is prohibited don't clobber anything.
        if not OPTIONS.dry_run:
            check_file_not_exists(dst_path_short)
    parent_folder = os.path.dirname(dst_path)
    if not os.path.exists(parent_folder):
        create_folder(parent_folder, quiet=quiet)
    if move:
        run(['mv', '-f', src_path_short, dst_path_short])
    else:
        run(['cp', '-af', src_path_short, dst_path_short])


def move_folder(src_path: Text,
                dst_path: Text,
                overwrite: bool = False,
                quiet: bool = False):
    """Move a folder to a fully-specified folder path, not a parent folder."""
    src_path_short = short_path(src_path, is_folder=True)
    dst_path_short = short_path(dst_path, is_folder=True)
    if not OPTIONS.dry_run:
        check_folder_exists(src_path_short)
    if overwrite:
        delete_folder(dst_path, quiet=quiet)
    else:
        if not OPTIONS.dry_run:
            check_folder_not_exists(dst_path_short)
    parent_folder = os.path.dirname(dst_path)
    if not os.path.exists(parent_folder):
        create_folder(parent_folder, quiet=quiet)
    run(['mv', '-f', src_path_short, dst_path_short])


def sync_folders(src_folder: Text,
                 dst_folder: Text,
                 exclude: List = None,
                 check_contents: bool = False,
                 show_files: bool = False,
                 quiet: bool = False):
    # Add the trailing slash for rsync. This works for remote paths too.
    src_folder = folder_path(src_folder)
    dst_folder = folder_path(dst_folder)
    if not OPTIONS.dry_run:
        check_folder_exists(src_folder)
    if not quiet:
        log_message('Folder sync.',
                    source=src_folder,
                    target=dst_folder,
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
    cmd_args.extend([src_folder, dst_folder])
    run(cmd_args)


@contextmanager
def temporary_working_folder(folder: Optional[Text], quiet: bool = False):
    """
    Change work folder and restore when done.

    Treats an empty or None folder, or when folder is the current work folder, a
    do-nothing operation. But at least the caller doesn't have to check.
    """
    restore_folder = os.getcwd()
    if folder and os.path.realpath(folder) != restore_folder:
        log_message('Change working directory.', folder, debug=quiet)
        os.chdir(folder)
    yield restore_folder
    if folder and os.path.realpath(folder) != restore_folder:
        log_message('Restore working directory.', restore_folder, debug=quiet)
        os.chdir(restore_folder)


def get_folder_stack(folder: Text) -> List[Text]:
    """
    Get a list of folders from top-most down to the one provided.

    TODO: This needs a little work for Windows compatibility!

    :param folder: bottom-most folder
    :return: top-to-bottom folder list
    """
    folders = []
    while True:
        head, tail = os.path.split(folder)
        if not tail:
            break
        folders.append(folder)
        folder = head
    return list(reversed(folders))


def resolve_paths_abs(root: Text, folders: Optional[List[Text]]) -> Iterator[Text]:
    """Generate folder sequence with absolute paths."""
    if folders:
        for folder in folders:
            if os.path.isabs(folder):
                yield folder
            else:
                yield os.path.join(root, folder)


class FileFilter:
    def __init__(self, source_folder: Text):
        self.source_folder = source_folder

    def accept(self, path: Text) -> bool:
        raise NotImplementedError


class ExcludesFilter(FileFilter):
    def __init__(self, source_folder: Text, excludes: List[Text]):
        if excludes:
            self.matcher = gitignore_parser.prepare_ignore_patterns(excludes, source_folder)
        else:
            self.matcher = None
        super().__init__(source_folder)

    def accept(self, path: Text) -> bool:
        if not self.matcher:
            return True
        return not self.matcher(path)


class GitignoreFilter(FileFilter):
    def __init__(self,  source_folder: Text):
        super().__init__(source_folder)
        gitignore_path = os.path.join(self.source_folder, '.gitignore')
        if os.path.isfile(gitignore_path):
            self.matcher = gitignore_parser.parse_gitignore(gitignore_path)
        else:
            self.matcher = None

    def accept(self, path: Text) -> bool:
        if not self.matcher:
            return True
        return not self.matcher(path)


def iterate_files(source_folder: Text) -> Iterator[Text]:
    discard_length = len(source_folder)
    if not source_folder.endswith(os.path.sep):
        discard_length += 1
    for dir_path, _sub_dir_paths, file_names in os.walk(source_folder):
        relative_dir_name = dir_path[discard_length:]
        for file_name in file_names:
            yield os.path.join(relative_dir_name, file_name)


def iterate_git_pending(source_folder: Text) -> Iterator[Text]:
    with temporary_working_folder(source_folder, quiet=True):
        git_proc = run(['git', 'status', '-s', '-uno'],
                       capture=True, run_always=True, quiet=True)
        for line in git_proc.stdout.split(os.linesep):
            path = line[3:]
            if os.path.isfile(path):
                yield path


def iterate_filtered_files(source_folder: Text,
                           excludes: List[Text] = None,
                           pending: bool = False,
                           gitignore: bool = False):
    if pending:
        file_iterator_function = iterate_git_pending
    else:
        file_iterator_function = iterate_files
    file_filters: List[FileFilter] = []
    if excludes:
        file_filters.append(ExcludesFilter(source_folder, excludes))
    if gitignore:
        file_filters.append(GitignoreFilter(source_folder))
    for path in file_iterator_function(source_folder):
        if all((file_filter.accept(path) for file_filter in file_filters)):
            yield path


def find_system_program(name: Text) -> Optional[Text]:
    """
    Search system PATH for named program.

    :param name: program name
    :return: path if found or None
    """
    for folder in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and (os.stat(path).st_mode & stat.S_IEXEC):
            return path
    return None


def choose_program_alternative(*programs: Any, required: bool = False) -> Optional[List]:
    """
    Search system PATH for one or more alternative programs, optionally with arguments.

    :param programs: program name(s) or argument lists/tuples
    :param required: fatal error if True and program was not found
    :return: first found program as a command argument list
    """
    for program in programs:
        name = program[0] if isinstance(program, (list, tuple)) else str(program)
        if find_system_program(name):
            return [str(arg) for arg in make_list(program)]
    if required:
        abort('Required program not found.', programs=programs)
    return None


def make_relative_path(path: Text, start: Text = None) -> Text:
    """
    Construct a relative path.

    Mainly a wrapper for os.path.relpath(), but it strips off leading './' to
    provided cleaner paths.

    :param path: path to convert to relative
    :param start: optional start path
    :return: relative path
    """
    rel_path = os.path.relpath(path, start=start)
    if rel_path == '.':
        return rel_path[1:]
    if rel_path.startswith('./'):
        return rel_path[2:]
    return rel_path
