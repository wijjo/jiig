"""
Git-related utilities.
"""

import os

from .filesystem import temporary_working_folder
from .process import run


def get_repo_url(repo_folder: str = None) -> str:
    """
    Get remote repository URL based on local repo folder.

    :param repo_folder: local repository folder (default: working folder)
    :return: remote repository URL
    """
    if repo_folder is None:
        repo_folder = os.getcwd()
    with temporary_working_folder(repo_folder):
        return run(['git', 'config', '--get', 'remote.origin.url'], capture=True).stdout.strip()


def repo_name_from_url(url: str) -> str:
    """
    Extract repository name from URL.

    :param url: repository URL
    :return: repository name
    """
    return url.split('.')[-2].split('/')[-1]
