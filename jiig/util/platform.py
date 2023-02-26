# Copyright (C) 2023, Steven Cooper
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
from typing import Sequence

from .collections import make_list
from .log import abort


class BaseSystemPackage(ABC):
    """Abstract base class for system packages and package bundles."""

    @abstractmethod
    def get_packages(self, platform_name: str) -> list[str]:
        ...

    @abstractmethod
    def get_check_executable(self, platform_name: str) -> str | None:
        ...


@dataclass
class SystemPackage(BaseSystemPackage):
    """System package installation data."""
    packages: str | Sequence[str]
    check_executable: str = None

    def get_packages(self, platform_name: str) -> list[str]:
        return make_list(self.packages)

    def get_check_executable(self, platform_name: str) -> str | None:
        return self.check_executable


@dataclass
class DevelopmentToolPackageBundle(BaseSystemPackage):
    """Development tool package bundle, adapted for target OS."""

    def get_packages(self, platform_name: str) -> list[str]:
        return DEVELOPMENT_PACKAGES[platform_name]

    def get_check_executable(self, platform_name: str) -> str | None:
        return 'gcc'


class VimPackageBundle(BaseSystemPackage):
    """Vim package bundle."""

    def get_packages(self, platform_name: str) -> list[str]:
        # TODO: Adapt for neovim, plugins, etc..
        return ['vim', 'vim-doc']

    def get_check_executable(self, platform_name: str) -> str | None:
        return 'vim'


class ZshPackageBundle(BaseSystemPackage):
    """Zsh package bundle."""

    def get_packages(self, platform_name: str) -> list[str]:
        # TODO: Adapt for plugins and other options.
        return ['zsh', 'zsh-doc']

    def get_check_executable(self, platform_name: str) -> str | None:
        return 'zsh'


@dataclass
class PackageManager:
    install_package: str
    refresh_database: str | None
    upgrade_all: str | None
    root_required: bool


@dataclass
class Platform:
    """Platform data."""
    name: str
    """Platform name."""
    recognition_pattern: str
    """Regular expression to test platform.version."""
    package_manager: PackageManager
    """Default package manager."""
    compiled_pattern: re.Pattern = field(init=False)
    """Automatically compiled recognition pattern."""
    check_command: str | None = None
    """Optional shell command to test if the platform matches."""

    def __post_init__(self):
        self.compiled_pattern = re.compile(self.recognition_pattern, re.IGNORECASE)


PACKAGE_MANAGERS: dict[str, PackageManager] = {
    # TODO: Untested.
    'apk': PackageManager(install_package='apk add --no-cache',
                          refresh_database='apk update',
                          upgrade_all='apk upgrade',
                          root_required=True),
    'apt': PackageManager(install_package='apt-get install -y',
                          refresh_database='apt-get update',
                          upgrade_all='apt-get upgrade -y',
                          root_required=True),
    # TODO: Untested.
    'dnf': PackageManager(install_package='dnf install -y',
                          refresh_database=None,
                          upgrade_all='dnf upgrade -y',
                          root_required=True),
    # TODO: Untested.
    'flatpak': PackageManager(install_package='flatpak install -y',
                              refresh_database=None,
                              upgrade_all=None,
                              root_required=True),
    'homebrew': PackageManager(install_package='brew install',
                               refresh_database=None,
                               upgrade_all='brew upgrade',
                               root_required=False),
    # TODO: Untested.
    'pacman': PackageManager(install_package='pacman -S --needed',
                             refresh_database='pacman -Sy',
                             upgrade_all='pacman -Syu',
                             root_required=True),
    # TODO: Untested.
    'snap': PackageManager(install_package='snap install',
                           refresh_database=None,
                           upgrade_all=None,
                           root_required=True),
    # TODO: Untested.
    'yum': PackageManager(install_package='yum install -y',
                          refresh_database=None,
                          upgrade_all='yum update -y',
                          root_required=True),
    # TODO: Untested.
    'zypper': PackageManager(install_package='zypper install -y',
                             refresh_database=None,
                             upgrade_all='zypper update -y',
                             root_required=True),
}

# TODO: make sure platform recognition patterns are correct.
SUPPORTED_PLATFORMS: dict[str, Platform] = {
    'debian': Platform(name='debian',
                       recognition_pattern=r'\b(:?Debian|Ubuntu)\b',
                       package_manager=PACKAGE_MANAGERS['apt'],
                       check_command='test -f /etc/debian_version'),
    'mac': Platform(name='mac',
                    recognition_pattern=r'\bDarwin\b',
                    package_manager=PACKAGE_MANAGERS['homebrew'],
                    check_command='test -d /Applications'),
    'fedora': Platform(name='fedora',
                       recognition_pattern=r'\bFedora\b',
                       package_manager=PACKAGE_MANAGERS['dnf'],
                       check_command='test -f /etc/fedora-release'),
    'centos': Platform(name='centos',
                       recognition_pattern=r'\bCentOS\b',
                       package_manager=PACKAGE_MANAGERS['yum']),
    'opensuse': Platform(name='opensuse',
                         recognition_pattern=r'\bOpenSUSE\b',
                         package_manager=PACKAGE_MANAGERS['zypper']),
    'arch': Platform(name='arch',
                     recognition_pattern=r'\bArch\b',
                     package_manager=PACKAGE_MANAGERS['pacman']),
    'alpine': Platform(name='alpine',
                       recognition_pattern=r'\bAlpine\b',
                       package_manager=PACKAGE_MANAGERS['apk']),
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
                        ) -> PackageManager | None:
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
                         ) -> Platform | None:
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
                 ) -> Platform | None:
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
