"""
Scripter provisioning script.
"""

from typing import List, Sequence, Union

from jiig.util.general import make_list
from jiig.util.options import Options
from jiig.util.process import shell_quote_path

from .script import Script


class ShellScript(Script):
    """Script that can perform local and remote provisioning tasks."""

    def create_folder(self, folder: str, need_root: bool = False, messages: dict = None):
        """
        Add folder creation to script.

        :param folder: folder to create
        :param need_root: requires root to create it successfully
        :param messages: output messages (defaults provided)
        """
        if messages is None:
            as_root = 'as root, ' if need_root else ''
            messages = {
                'before': f'Creating folder ({as_root}as needed): {folder}',
                'skip': f'Folder "{folder}" already exists.',
            }
        self.action(
            self._wrap_command(f'mkdir -p {folder}', need_root=need_root),
            predicate=f'[[ ! -d {folder} ]]',
            messages=messages,
        )

    def create_parent_folder(self, path: str, need_root: bool = False, messages: dict = None):
        """
        Add parent folder creation to script.

        :param path: file or folder path that will be a child of new parent folder
        :param need_root: requires root to create it successfully
        :param messages: output messages (defaults provided)
        """
        if messages is None:
            as_root = 'as root, ' if need_root else ''
            messages = {
                'before': f'Creating parent folder ({as_root}as needed) for: {path}',
                'skip': f'Parent folder for "{path}" already exists.',
            }
        quoted_path = shell_quote_path(path)
        self.action(
            self._wrap_command(f'mkdir -p $(dirname {quoted_path})', need_root=need_root),
            predicate=f'[[ ! -d $(dirname {quoted_path}) ]]',
            messages=messages,
        )

    def delete_folder(self, folder: str, need_root: bool = False, messages: dict = None):
        """
        Add folder deletion to script.

        :param folder: folder to delete
        :param need_root: requires root to delete it successfully
        :param messages: output messages (defaults provided)
        """
        redirect = ' 2> /dev/null' if not Options.debug else ''
        if messages is None:
            as_root = 'as root, ' if need_root else ''
            messages = {
                'before': f'Deleting folder ({as_root}if it exists): {folder}',
                'skip': f'Folder "{folder}" does not exist.',
            }
        quoted_folder = shell_quote_path(folder)
        self.action(
            self._wrap_command(f'rm -rf {quoted_folder}{redirect}', need_root=need_root),
            predicate=f'[[ -d {quoted_folder} ]]',
            messages=messages,
        )

    def delete_file(self, file: str, need_root: bool = False, messages: dict = None):
        """
        Add folder deletion to script.

        :param file: file to delete
        :param need_root: requires root to successfully delete
        :param messages: output messages (defaults provided)
        """
        quoted_file = shell_quote_path(file)
        if messages is None:
            as_root = 'as root, ' if need_root else ''
            messages = {
                'before': f'Deleting file ({as_root}as needed): {file}',
                'skip': f'File {quoted_file} does not exist.',
            }
        verbose_option = 'v' if Options.debug or Options.verbose else ''
        self.action(
            self._wrap_command(f'rm -f{verbose_option} {quoted_file}', need_root=need_root),
            predicate=f'[[ -e {quoted_file} ]]',
            messages=messages,
        )

    def symlink(self, source: str, target: str, need_root: bool = False, messages: dict = None):
        """
        Add symbolic link creation to script.

        :param source: source path
        :param target: target symlink path
        :param need_root: requires root to delete it successfully
        :param messages: output messages (defaults provided)
        """
        if messages is None:
            as_root = 'as root, ' if need_root else ''
            messages = {
                'before': f'Creating symbolic link ({as_root}as needed): {source} -> {target}',
                'skip': f'Symbolic link target "{target}" already exists.',
            }
        self.action(
            self._wrap_command(f'ln -s {source} {target}', need_root=need_root),
            predicate=f'[[ ! -e {target} ]]',
            messages=messages,
        )

    def synchronize_files(self,
                          source_path_or_paths: Union[str, Sequence[str]],
                          target_path: str,
                          skip_existing: bool = False,
                          quiet: bool = False,
                          ):
        """
        Front end to scripted rsync command with simplified options.

        As with rsync itself, trailing slashes should be used when synchronizing
        folders.

        :param source_path_or_paths: source path(s) using rsync syntax if host is specified
        :param target_path: target path using rsync syntax if host is specified
        :param skip_existing: don't overwrite existing files
        :param quiet: suppress non-error messages
        """
        options: List[str] = ['--archive']
        if Options.dry_run:
            options.append('--dry-run')
        if Options.debug or Options.verbose:
            options.append('--verbose')
        elif quiet:
            options.append('--quiet')
        if skip_existing:
            options.append('--ignore-existing')
        option_string = f'{" ".join(options)} ' if options else ''
        quoted_target_path = shell_quote_path(target_path)
        quoted_source_paths = ' '.join([
            shell_quote_path(path) for path in make_list(source_path_or_paths)])
        quoted_target_path = quoted_target_path
        quoted_source_paths = quoted_source_paths
        option_string = option_string
        self.action(
            f'rsync {option_string}{quoted_source_paths} {quoted_target_path}',
            messages={
                'before': f'Synchronizing files: {quoted_source_paths} -> {quoted_target_path}',
            }
        )
