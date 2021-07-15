"""
Scripter for file and folder actions.
"""

from jiig import OPTIONS, Script
from jiig.util.process import shell_quote_path


def script_folder_creation(script: Script,
                           folder: str,
                           need_root: bool = False,
                           messages: dict = None,
                           ):
    """
    Add folder creation to script.

    :param script: script to receive actions
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
    with script.block(
        predicate=f'[[ ! -d {folder} ]]',
        messages=messages,
    ):
        script.action(
            script.wrap_command(f'mkdir -p {folder}', need_root=need_root),
            messages=messages,
        )


def script_parent_folder_creation(script: Script,
                                  path: str,
                                  need_root: bool = False,
                                  messages: dict = None,
                                  ):
    """
    Add parent folder creation to script.

    :param script: script to receive actions
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
    with script.block(
        predicate=f'[[ ! -d $(dirname {quoted_path}) ]]',
        messages=messages,
    ):
        script.action(
            script.wrap_command(f'mkdir -p $(dirname {quoted_path})', need_root=need_root),
            messages=messages,
        )


def script_folder_deletion(script: Script,
                           folder: str,
                           need_root: bool = False,
                           messages: dict = None,
                           ):
    """
    Add folder deletion to script.

    :param script: script to receive actions
    :param folder: folder to delete
    :param need_root: requires root to delete it successfully
    :param messages: output messages (defaults provided)
    """
    redirect = ' 2> /dev/null' if not OPTIONS.debug else ''
    if messages is None:
        as_root = 'as root, ' if need_root else ''
        messages = {
            'before': f'Deleting folder ({as_root}if it exists): {folder}',
            'skip': f'Folder "{folder}" does not exist.',
        }
    quoted_folder = shell_quote_path(folder)
    with script.block(
        predicate=f'[[ -d {quoted_folder} ]]',
        messages=messages,
    ):
        script.action(
            script.wrap_command(f'rm -rf {quoted_folder}{redirect}', need_root=need_root),
            messages=messages,
        )
