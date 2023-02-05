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

"""
Global option flags for util library.
"""

import os


def _env_boolean(name: str) -> bool:
    return os.environ.get(name, '').lower() in ['yes', 'true', '1']


class Options:
    """
    Jiig utility library options, with environment overrides.

    Read access is through properties to allow environment variables to
    influence option settings.

    Write access is through set_...() methods to prevent some accidental
    overwrites.
    """

    def __init__(self):
        """Options constructor."""
        # None for booleans indicate that initialization hasn't taken place.
        self._verbose: bool | None = None
        self._debug: bool | None = None
        self._dry_run: bool | None = None
        self._pause: bool | None = None
        self._keep_files: bool | None = None
        self._message_indent = '   '
        self._column_separator = '  '
        self._env_verbose: bool = _env_boolean('JIIG_VERBOSE')
        self._env_debug: bool = _env_boolean('JIIG_DEBUG')
        self._env_dry_run: bool = _env_boolean('JIIG_DRY_RUN')
        self._env_pause: bool = _env_boolean('JIIG_PAUSE')
        self._env_keep_files: bool = _env_boolean('JIIG_KEEP_FILES')

    @property
    def is_initialized(self) -> bool:
        """
        Indicates whether or not options were updated externally.

        :return: True if options are considered initialized
        """
        return self._verbose is not None

    @property
    def verbose(self) -> bool:
        """
        Read-only access to verbose option with environment override.

        :return: True if verbosity is enabled
        """
        return self._verbose or self._env_verbose

    @property
    def debug(self) -> bool:
        """
        Read-only access to debug option with environment override.

        :return: True if debugging is enabled
        """
        return self._debug or self._env_debug

    @property
    def dry_run(self) -> bool:
        """
        Read-only access to dry-run option with environment override.

        :return: True if dry-run is enabled
        """
        return self._dry_run or self._env_dry_run

    @property
    def pause(self) -> bool:
        """
        Read-only access to pause option with environment override.

        :return: True if pausing is enabled
        """
        return self._pause or self._env_pause

    @property
    def keep_files(self) -> bool:
        """
        Read-only access to keep-files option with environment override.

        :return: True if file preservation is enabled
        """
        return self._keep_files or self._env_keep_files

    @property
    def message_indent(self) -> str:
        """
        Read-only access to message indent string.

        :return: message indent string
        """
        return self._message_indent

    @property
    def column_separator(self) -> str:
        """
        Read-only access to table column separator string.

        :return: table column separator string
        """
        return self._column_separator

    def set_verbose(self, enabled: bool):
        """
        Update verbose option.

        :param enabled: enabled if True
        """
        self._verbose = enabled

    def set_debug(self, enabled: bool):
        """
        Update debug option.

        :param enabled: enabled if True
        """
        self._debug = enabled

    def set_dry_run(self, enabled: bool):
        """
        Update dry-run option.

        :param enabled: enabled if True
        """
        self._dry_run = enabled

    def set_pause(self, enabled: bool):
        """
        Update pause option.

        :param enabled: enabled if True
        """
        self._pause = enabled

    def set_keep_files(self, enabled: bool):
        """
        Update keep-files option.

        :param enabled: enabled if True
        """
        self._keep_files = enabled

    def set_message_indent(self, text: str):
        """
        Update message indent string.

        :param text: updated string
        """
        self._message_indent = text

    def set_column_separator(self, text: str):
        """
        Update column separator string.

        :param text: updated string
        """
        self._column_separator = text

    def copy(self, other: 'Options'):
        """
        Copy option settings from another instance.

        :param other: other Options instance to copy from
        """
        self._verbose: bool | None = other._verbose
        self._debug: bool | None = other._debug
        self._dry_run: bool | None = other._dry_run
        self._pause: bool | None = other._pause
        self._keep_files: bool | None = other._keep_files
        self._message_indent = other._message_indent
        self._column_separator = other._column_separator


OPTIONS = Options()
