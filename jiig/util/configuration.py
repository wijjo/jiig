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
import os
import tomllib
from pathlib import Path

from .collections import AttributeDictionary
from .stream import open_input_file


class Configuration(AttributeDictionary):
    pass


def load_configuration(config_path: Path | str,
                       ignore_decode_error: bool = False,
                       writeable: bool = False,
                       defaults: dict = None,
                       config_format: str = None,
                       ) -> Configuration | None:
    """Read configuration file in any supported format.

    Configuration format may be explicitly specified with the `config_format`
    parameter or deduced by sampling configuration text.

    "#..." comments are always stripped out, even for JSON files.

    Expect configuration data to produce a dictionary.

    Args:
        config_path: configuration file path
        ignore_decode_error: ignore decode errors and return None if True
        writeable: allow updates if True
        defaults: optional dictionary providing defaults for missing elements
        config_format: optional explicit format, i.e. 'json' or 'toml'

    Returns:
        dictionary data or None if ignore_decode_error is True and decoding
        failed

    Raises:
        TypeError: if data is not a dictionary
        ValueError: if decoding fails
        IOError: if a problem occurs while opening or reading the file
        OSError: if an OS error occurs while accessing the file
    """
    lines: list[str] = []
    for line in open_input_file(config_path):
        line: str = line.rstrip()
        if line.lstrip().startswith('#'):
            line = ''   # Keep blank lines for comments for line numbers in errors.
        lines.append(line)
        if line and config_format is None:
            if line.startswith('{'):
                config_format = 'json'
            elif line.startswith('['):
                config_format = 'toml'
            else:
                raise TypeError('Format does not appear to be either JSON or TOML.')
    data_string = os.linesep.join(lines)
    match config_format.lower():
        case 'json':
            try:
                config_data = json.loads(data_string)
            except json.JSONDecodeError as decode_exc:
                if ignore_decode_error:
                    return None
                raise ValueError(f'Unable to parse JSON configuration file at line'
                                 f' {decode_exc.lineno}, column {decode_exc.colno}:'
                                 f' {config_path}: {decode_exc.msg}')
        case 'toml':
            try:
                config_data = tomllib.loads(data_string)
            except tomllib.TOMLDecodeError as decode_exc:
                if ignore_decode_error:
                    return None
                raise ValueError(f'Unable to parse TOML configuration file:'
                                 f' {config_path}: {decode_exc}')
        case _:
            raise TypeError('Format must be either "json" or "toml".')
    if defaults:
        def _update_recursive(item_data: dict, item_defaults: dict):
            for item_name, item_value in item_defaults.items():
                if item_name not in item_data:
                    item_data[item_name] = item_value
                elif isinstance(item_value, dict):
                    _update_recursive(item_data[item_name], item_value)
        _update_recursive(config_data, defaults)
    return Configuration.new(config_data, no_defaults=True, read_only=not writeable)
