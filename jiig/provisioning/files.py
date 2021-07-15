"""
File provisioning.
"""

from typing import List, Sequence, Union

from jiig import OPTIONS, Script
from jiig.util.general import make_list
from jiig.util.process import shell_quote_path


def script_file_deletion(script: Script,
                         file: str,
                         need_root: bool = False,
                         messages: dict = None,
                         ):
    """
    Add folder deletion to script.

    :param script: script to receive actions
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
    verbose_option = 'v' if OPTIONS.debug or OPTIONS.verbose else ''
    with script.block(
        predicate=f'[[ -e {quoted_file} ]]',
        messages=messages,
    ):
        script.action(
            script.wrap_command(f'rm -f{verbose_option} {quoted_file}', need_root=need_root),
            messages=messages,
        )


def script_symlink_creation(script: Script,
                            source: str,
                            target: str,
                            need_root: bool = False,
                            messages: dict = None,
                            ):
    """
    Add symbolic link creation to script.

    :param script: script to receive actions
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
    with script.block(
        predicate=f'[[ ! -e {target} ]]',
        messages=messages,
    ):
        script.action(
            script.wrap_command(f'ln -s {source} {target}', need_root=need_root),
            messages=messages,
        )


def script_file_deployment(script: Script,
                           source_path_or_paths: Union[str, Sequence[str]],
                           target_path: str,
                           skip_existing: bool = False,
                           quiet: bool = False,
                           ):
    """
    Front end to scripted rsync command with simplified options.

    As with rsync itself, trailing slashes should be used when synchronizing
    folders.

    :param script: script to receive actions
    :param source_path_or_paths: source path(s) using rsync syntax if host is specified
    :param target_path: target path using rsync syntax if host is specified
    :param skip_existing: don't overwrite existing files
    :param quiet: suppress non-error messages
    """
    options: List[str] = ['--archive']
    if OPTIONS.dry_run:
        options.append('--dry-run')
    if OPTIONS.debug or OPTIONS.verbose:
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
    script.action(
        f'rsync {option_string}{quoted_source_paths} {quoted_target_path}',
        messages={
            'before': f'Synchronizing files: {quoted_source_paths} -> {quoted_target_path}',
        }
    )
