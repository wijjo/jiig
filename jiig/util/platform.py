# Copyright (C) 2022, Steven Cooper
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
Platform-related utility functions and classes.
"""

import platform
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Sequence

from .general import make_list
from .log import abort


class BaseSystemPackage(ABC):
    """Abstract base class for system packages and package bundles."""

    @abstractmethod
    def get_packages(self, platform_name: str) -> list[str]:
        ...

    @abstractmethod
    def get_check_executable(self, platform_name: str) -> Optional[str]:
        ...


@dataclass
class SystemPackage(BaseSystemPackage):
    """System package installation data."""
    packages: str | Sequence[str]
    check_executable: str = None

    def get_packages(self, platform_name: str) -> list[str]:
        return make_list(self.packages)

    def get_check_executable(self, platform_name: str) -> Optional[str]:
        return self.check_executable


@dataclass
class DevelopmentToolPackageBundle(BaseSystemPackage):
    """Development tool package bundle, adapted for target OS."""

    def get_packages(self, platform_name: str) -> list[str]:
        return DEVELOPMENT_PACKAGES[platform_name]

    def get_check_executable(self, platform_name: str) -> Optional[str]:
        return 'gcc'


class VimPackageBundle(BaseSystemPackage):
    """Vim package bundle."""

    def get_packages(self, platform_name: str) -> list[str]:
        # TODO: Adapt for neovim, plugins, etc..
        return ['vim', 'vim-doc']

    def get_check_executable(self, platform_name: str) -> Optional[str]:
        return 'vim'


class ZshPackageBundle(BaseSystemPackage):
    """Zsh package bundle."""

    def get_packages(self, platform_name: str) -> list[str]:
        # TODO: Adapt for plugins and other options.
        return ['zsh', 'zsh-doc']

    def get_check_executable(self, platform_name: str) -> Optional[str]:
        return 'zsh'


@dataclass
class PackageManager:
    install_command: str
    update_command: Optional[str]
    root_required: bool


@dataclass
class Platform:
    """Platform data."""
    name: str
    recognition_pattern: str
    package_manager: PackageManager
    compiled_pattern: re.Pattern = field(init=False)

    def __post_init__(self):
        self.compiled_pattern = re.compile(self.recognition_pattern, re.IGNORECASE)


PACKAGE_MANAGERS: dict[str, PackageManager] = {
    # TODO: Check.
    'apk': PackageManager(install_command='apk add --no-cache',
                          update_command='apk update',
                          root_required=True),
    'apt': PackageManager(install_command='apt-get install -y',
                          update_command='apt-get update',
                          root_required=True),
    # TODO: Check.
    'dnf': PackageManager(install_command='dnf install -y',
                          update_command=None,
                          root_required=True),
    'homebrew': PackageManager(install_command='brew install',
                               update_command=None,
                               root_required=False),
    # TODO: Check.
    'pacman': PackageManager(install_command='pacman -S --needed',
                             update_command='pacman -Sy',
                             root_required=True),
    # TODO: Check.
    'yum': PackageManager(install_command='yum install -y',
                          update_command=None,
                          root_required=True),
    # TODO: Check.
    'zypper': PackageManager(install_command='zypper install -y',
                             update_command=None,
                             root_required=True),
}

# TODO: make sure platform recognition patterns are correct.
SUPPORTED_PLATFORMS: dict[str, Platform] = {
    'debian': Platform('debian', r'\b(:?Debian|Ubuntu)\b', PACKAGE_MANAGERS['apt']),
    'mac': Platform('mac', r'\bDarwin\b', PACKAGE_MANAGERS['homebrew']),
    'centos': Platform('centos', r'\bCentOS\b', PACKAGE_MANAGERS['yum']),
    'fedora': Platform('fedora', r'\bFedora\b', PACKAGE_MANAGERS['dnf']),
    'opensuse': Platform('opensuse', r'\bOpenSUSE\b', PACKAGE_MANAGERS['zypper']),
    'arch': Platform('arch', r'\bArch\b', PACKAGE_MANAGERS['pacman']),
    'alpine': Platform('alpine', r'\bAlpine\b', PACKAGE_MANAGERS['apk']),
}


# See https://github.com/pyenv/pyenv/wiki#suggested-build-environment
DEVELOPMENT_PACKAGES: dict[str, list[str]] = {
    'debian': [
        'make', 'build-essential', 'wget', 'curl', 'llvm', 'xz-utils', 'libssl-dev',
        'zlib1g-dev', 'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'libncursesw5-dev',
        'tk-dev', 'libxml2-dev', 'libxmlsec1-dev', 'libffi-dev', 'liblzma-dev',
    ],
    'mac': [
        'openssl', 'readline', 'sqlite3', 'xz', 'zlib', 'tcl-tk',
    ],
    'centos': [
        'gcc', 'zlib-devel', 'bzip2', 'bzip2-devel', 'readline-devel',
        'sqlite', 'sqlite-devel', 'openssl-devel', 'tk-devel', 'libffi-devel', 'xz-devel',
    ],
    'fedora': [
        'make', 'gcc', 'zlib-devel', 'bzip2', 'bzip2-devel', 'readline-devel',
        'sqlite', 'sqlite-devel', 'openssl-devel', 'tk-devel', 'libffi-devel', 'xz-devel',
    ],
    'opensuse': [
        'gcc', 'automake', 'bzip2', 'libbz2-devel', 'xz', 'xz-devel', 'openssl-devel',
        'ncurses-devel', 'readline-devel', 'zlib-devel', 'tk-devel', 'libffi-devel', 'sqlite3-devel',
    ],
    'arch': [
        'base-devel', 'openssl', 'zlib', 'xz', 'tk',
    ],
    'alpine': [
        'git', 'bash', 'build-base', 'libffi-dev', 'openssl-dev',
        'bzip2-dev', 'zlib-dev', 'xz-dev', 'readline-dev', 'sqlite-dev', 'tk-dev',
    ],
}


def get_package_manager(package_manager_name: str,
                        checked: bool = False,
                        ) -> Optional[PackageManager]:
    """
    Look up package manager by name.

    :param package_manager_name: package manager name
    :param checked: abort if package manager not found
    :return: package manager data or None if not found
    """
    manager = PACKAGE_MANAGERS.get(package_manager_name)
    if manager is None and checked:
        abort(f'Unsupported package manager: {package_manager_name}')
    return manager


def get_working_platform(checked: bool = False,
                         ) -> Optional[Platform]:
    """
    Look up working platform information.

    :param checked: abort if not a supported platform type
    :return: Platform data or None if not a supported platform type
    """
    version = platform.version()
    for platform_name, supported_platform in SUPPORTED_PLATFORMS.items():
        if supported_platform.compiled_pattern.search(version):
            return supported_platform
    if checked:
        abort('Unsupported local platform.')
    return None


def get_platform(platform_name: str,
                 checked: bool = False,
                 ) -> Optional[Platform]:
    """
    Look up platform information by name.

    :param platform_name: platform name
    :param checked: abort if not a supported platform type
    :return: Platform data or None if not a supported platform type
    """
    resolved_platform = SUPPORTED_PLATFORMS.get(platform_name)
    if resolved_platform is None and checked:
        abort(f'Unsupported platform: {platform_name}')
    return resolved_platform
