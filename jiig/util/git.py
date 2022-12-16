# Copyright (C) 2020-2022, Steven Cooper
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
        return run(['git', 'config', '--get', 'remote.origin.url'],
                   capture=True,
                   ).stdout.strip()


def repo_name_from_url(url: str) -> str:
    """
    Extract repository name from URL.

    :param url: repository URL
    :return: repository name
    """
    return url.split('.')[-2].split('/')[-1]
