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

"""Git-related utilities."""

import os
from typing import Iterable

from .filesystem import temporary_working_folder
from .process import run


def get_repo_url(repo_folder: str = None) -> str:
    """Get remote repository URL based on local repo folder.

    Args:
        repo_folder: local repository folder (default: working folder)

    Returns:
        remote repository URL
    """
    if repo_folder is None:
        repo_folder = os.getcwd()
    with temporary_working_folder(repo_folder):
        return run(['git', 'config', '--get', 'remote.origin.url'],
                   capture=True,
                   ).stdout.strip()


def repo_name_from_url(url: str) -> str:
    """Extract repository name from URL.

    Args:
        url: repository URL

    Returns:
        repository name
    """
    name = url.split('/')[-1]
    if name.endswith('.git'):
        name = name[:-4]
    return name


def find_url_by_name(urls: Iterable[str],
                     name: str,
                     partial: bool = False,
                     ) -> str | None:
    """Find URL by full or partial repository name.

    Args:
        urls: iterable URLs to search
        name: full or partial name to search for
        partial: accept partial matches

    Returns:
        matched URL or None if not found
    """
    for url in urls:
        extracted_name = repo_name_from_url(url)
        if partial:
            name_parts = url.split('/')[-1].split('.')
            while name_parts:
                extracted_name = '.'.join(name_parts)
                if name.lower() == extracted_name.lower():
                    return url
                name_parts = name_parts[:-1]
        else:
            if extracted_name == name:
                return url
    return None
