"""Path manipulation utilities."""

import os
import re
import stat
from contextlib import contextmanager
from glob import glob
from string import Template
from typing import Text, List, Optional, Dict, Iterator

from thirdparty.gitignore_parser.gitignore_parser import parse_gitignore, prepare_ignore_patterns

from jiig.internal import global_data
from .console import abort, log_error, log_heading, log_message, log_warning
from .process import run

REMOTE_PATH_REGEX = re.compile(r'^([\w\d.@-]+):([\w\d_-~/]+)$')
TEMPLATE_FOLDER_SYMBOL = re.compile(global_data.TEMPLATE_FOLDER_SYMBOL_PATTERN)


def folder_path(path):
    if not path.endswith('/'):
        path += '/'
    return path


def is_remote_path(path: Text) -> bool:
    return bool(REMOTE_PATH_REGEX.match(path))


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
    if path.startswith(working_folder):
        path = path[len(working_folder) + 1:]
    else:
        parent_folder = os.path.dirname(working_folder)
        if path.startswith(parent_folder):
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


def create_folder(path: Text, delete_existing: bool = False, quiet: bool = False):
    path = short_path(path, is_folder=True)
    if delete_existing:
        delete_folder(path, quiet=quiet)
    if not os.path.exists(path):
        if not quiet:
            log_message('Create folder.', folder_path(path))
        run(['mkdir', '-p', path])
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
    if not global_data.DRY_RUN:
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
    src_path_short = short_path(src_path, is_folder=False)
    dst_path_short = short_path(dst_path, is_folder=False)
    if not global_data.DRY_RUN:
        check_file_exists(src_path_short)
    if overwrite:
        # If overwriting is allowed a file (only) can be clobbered.
        if os.path.exists(dst_path) and not global_data.DRY_RUN:
            check_file_exists(dst_path)
    else:
        # If overwriting is prohibited don't clobber anything.
        if not global_data.DRY_RUN:
            check_file_not_exists(dst_path_short)
    parent_folder = os.path.dirname(dst_path)
    if not os.path.exists(parent_folder):
        create_folder(parent_folder, quiet=quiet)
    run(['mv', '-f', src_path_short, dst_path_short])


def move_folder(src_path: Text,
                dst_path: Text,
                overwrite: bool = False,
                quiet: bool = False):
    """Move a folder to a fully-specified folder path, not a parent folder."""
    src_path_short = short_path(src_path, is_folder=True)
    dst_path_short = short_path(dst_path, is_folder=True)
    if not global_data.DRY_RUN:
        check_folder_exists(src_path_short)
    if overwrite:
        delete_folder(dst_path, quiet=quiet)
    else:
        if not global_data.DRY_RUN:
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
    if not global_data.DRY_RUN:
        check_folder_exists(src_folder)
    if not quiet:
        log_message('Folder sync.',
                    source=src_folder,
                    target=dst_folder,
                    exclude=exclude or [])
    cmd_args = ['rsync']
    if global_data.DRY_RUN:
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
def chdir(folder: Optional[Text], quiet: bool = False):
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


def expand_template(source_path: Text,
                    target_path: Text,
                    overwrite: bool = False,
                    executable: bool = False,
                    symbols: Dict = None,
                    source_relative_to: Text = None,
                    target_relative_to: Text = None):
    if source_relative_to:
        short_source_path = source_path[len(source_relative_to) + 1:]
    else:
        short_source_path = short_path(source_path)
    if target_relative_to:
        short_target_path = target_path[len(target_relative_to) + 1:]
    else:
        short_target_path = short_path(target_path)
    symbols = symbols or {}
    if not global_data.DRY_RUN:
        check_file_exists(source_path)
    if os.path.exists(target_path):
        if not os.path.isfile(target_path):
            abort('Template expansion target exists, but is not a file',
                  short_target_path)
        if not overwrite:
            log_message('Template expansion target exists - skipping',
                        short_target_path)
            return
    log_message('Generate from template.',
                source=short_source_path,
                target=short_target_path)
    if not global_data.DRY_RUN:
        try:
            with open(source_path, encoding='utf-8') as src_file:
                with open(target_path, 'w', encoding='utf-8') as target_file:
                    output_text = Template(src_file.read()).substitute(symbols)
                    target_file.write(output_text)
                if executable:
                    os.system('chmod +x {}'.format(target_path))
        except KeyError as exc_key_error:
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except (IOError, OSError) as exc_remove:
                    log_warning('Unable to remove failed target file.',
                                short_target_path,
                                exception=exc_remove)
            abort('Missing template symbol',
                  source=short_source_path,
                  symbol=exc_key_error)
        except (IOError, OSError) as exc_write_error:
            abort('Template expansion failed',
                  source=short_source_path,
                  target=short_target_path,
                  exception=exc_write_error)


def expand_templates(source_glob: Text,
                     target_folder_path: Text,
                     overwrite: bool = False,
                     executable: bool = False,
                     symbols: Dict = None):
    for source_path in glob(source_glob):
        target_path = os.path.join(target_folder_path, os.path.basename(source_path))
        expand_template(source_path,
                        target_path,
                        overwrite=overwrite,
                        executable=executable,
                        symbols=symbols)


def expand_template_path(source_path: Text, symbols: Dict) -> Text:
    """
    Expand name symbols in path.

    :param source_path: source path with potential symbols to expand
    :param symbols: symbol substitution dictionary
    :return: output path with symbols expanded
    """
    name_parts = []
    pos = 0
    for match in TEMPLATE_FOLDER_SYMBOL.finditer(source_path):
        name = match.group(1)
        start_pos, end_pos = match.span()
        if start_pos > pos:
            name_parts.append(source_path[pos:start_pos])
        if name in symbols:
            name_parts.append(symbols[name])
        else:
            log_error(f'Symbol "{name}" not found for path template "{source_path}".')
            name_parts.append(source_path[start_pos:end_pos])
        pos = end_pos
    if pos < len(source_path):
        name_parts.append(source_path[pos:])
    return ''.join(name_parts)


def expand_template_folder(template_folder: Text,
                           target_folder: Text,
                           overwrite: bool = False,
                           symbols: Dict = None):
    """
    Recursively populate a target folder based on a template folder.

    Note that .template* extensions are removed with special extensions handled
    for generating dot name prefixes and setting executable permissions.

    Source folder names may take advantage of symbol expansion by using special
    syntax for name substitution. Target folder names will receive any
    substituted symbols.

    :param template_folder: path to template source folder
    :param target_folder: path to target folder
    :param overwrite: overwrite files if True
    :param symbols: symbols for template expansion
    :return:
    """
    symbols = symbols or {}
    if not os.path.isdir(template_folder):
        abort('Template source folder does not exist',
              source_folder=folder_path(template_folder))
    if os.path.exists(target_folder):
        if not os.path.isdir(target_folder):
            abort('Template target folder exists, but is not a folder',
                  target_folder=target_folder)
    log_heading(2, f'Expanding templates.')
    log_message(None, template_folder=template_folder, target_folder=target_folder)
    create_folder(target_folder)
    for walk_source_folder, _walk_sub_folders, walk_file_names in os.walk(template_folder):
        relative_folder = walk_source_folder[len(template_folder) + 1:]
        expanded_folder = expand_template_path(relative_folder, symbols)
        walk_target_folder = os.path.join(target_folder, expanded_folder)
        create_folder(walk_target_folder)
        for file_name in walk_file_names:
            source_path = os.path.join(walk_source_folder, file_name)
            stripped_file_name, extension = os.path.splitext(file_name)
            if extension in global_data.ALL_TEMPLATE_EXTENSIONS:
                if extension == global_data.TEMPLATE_EXTENSION_DOT:
                    stripped_file_name = '.' + stripped_file_name
                expanded_file_name = expand_template_path(stripped_file_name, symbols)
                target_path = os.path.join(walk_target_folder, expanded_file_name)
                executable = extension == global_data.TEMPLATE_EXTENSION_EXE
                expand_template(source_path,
                                target_path,
                                overwrite=overwrite,
                                executable=executable,
                                symbols=symbols,
                                source_relative_to=template_folder,
                                target_relative_to=target_folder)
            else:
                copy_files(source_path, walk_target_folder)


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
            self.matcher = prepare_ignore_patterns(excludes, source_folder)
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
            self.matcher = parse_gitignore(gitignore_path)
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
    with chdir(source_folder, quiet=True):
        git_proc = run(['git', 'status', '-s', '-uno'], capture=True)
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
    """Return path of system program if found or None if not."""
    for folder in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and (os.stat(path).st_mode & stat.S_IEXEC):
            return path
    return None
