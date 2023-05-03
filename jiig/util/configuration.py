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

"""Read/write TOML and JSON configuration files."""

import json
import tomllib
from pathlib import Path

from .collections import AttributeDictionary


def read_toml_configuration(config_path: Path | str,
                            ignore_decode_error: bool = False,
                            ) -> AttributeDictionary | None:
    """Read TOML format configuration file.

    Expect configuration data to produce a dictionary.

    Args:
        config_path: configuration file path
        ignore_decode_error: ignore decode errors and return None if True

    Returns:
        dictionary data or None if ignore_decode_error is True and decoding
        failed

    Raises:
        TypeError: if data is not a dictionary
        ValueError: if decoding fails
        IOError: if a problem occurs while opening or reading the file
        OSError: if an OS error occurs while accessing the file
    """
    with open(config_path, 'rb') as config_file:
        try:
            config_data = tomllib.load(config_file)
            if not isinstance(config_data, dict):
                raise TypeError(f'TOML configuration file data is not a'
                                f' dictionary: {config_path}')
            return AttributeDictionary.new(config_data)
        except tomllib.TOMLDecodeError as decode_exc:
            if ignore_decode_error:
                return None
            raise ValueError(f'Unable to parse TOML configuration file:'
                             f' {config_path}: {decode_exc}')


def read_json_configuration(config_path: Path | str,
                            skip_file_header: bool = False,
                            ignore_decode_error: bool = False,
                            ) -> AttributeDictionary | None:
    """Read JSON format configuration file.

    Expect configuration data to produce a dictionary.

    Args:
        config_path: configuration file path
        skip_file_header: skip to first line that starts with "{"
        ignore_decode_error: ignore decode errors and return None if True

    Returns:
        dictionary data or None if ignore_decode_error is True and decoding
        failed

    Raises:
        TypeError: if data is not a dictionary
        ValueError: if decoding fails
        IOError: if a problem occurs while opening or reading the file
        OSError: if an OS error occurs while accessing the file
    """
    with open(config_path, encoding='utf-8') as config_file:
        lines = config_file.readlines()
        skipped = 0
        if skip_file_header:
            for idx, line in enumerate(lines):
                if line.lstrip().startswith('{'):
                    lines = lines[idx:]
                    break
                skipped += 1
        data_string = ''.join(lines)
        try:
            config_data = json.loads(data_string)
            if not isinstance(config_data, dict):
                raise TypeError(f'JSON configuration file data is not a'
                                f' dictionary: {config_path}')
            return AttributeDictionary.new(config_data)
        except json.JSONDecodeError as decode_exc:
            if ignore_decode_error:
                return None
            raise ValueError(f'Unable to parse JSON configuration file at line'
                             f' {decode_exc.lineno + skipped}, column {decode_exc.colno}:'
                             f' {config_path}: {decode_exc.msg}')
