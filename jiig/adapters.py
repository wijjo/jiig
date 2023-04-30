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

"""Jiig argument adapters, converters, etc..

Used for task field validation and conversion.
"""

import base64
import binascii
import os
from pathlib import Path
from time import mktime
from typing import Any

from .types import ArgumentAdapter
from .util.date_time import parse_date_time, parse_time_interval, apply_date_time_delta_string


def b64_decode(value: str) -> str:
    """Decode base64 string.

    Args:
        value: input base64 string

    Returns:
        output utf-8 string
    """
    try:
        return base64.standard_b64decode(value).decode('utf-8')
    except binascii.Error as exc:
        # Wrap as ValueError, because binascii.Error will not be caught for the argument.
        raise ValueError(str(exc))


def b64_encode(value: str) -> str:
    """Encode string to base64.

    Args:
        value: input string

    Returns:
        output base64 string
    """
    try:
        return base64.standard_b64encode(bytes(value, 'utf-8')).decode('utf-8')
    except binascii.Error as exc:
        # Wrap as ValueError, because binascii.Error will not be caught for the argument.
        raise ValueError(str(exc))


def choices(*valid_values: Any) -> ArgumentAdapter:
    """Adapter factory that limits value to a set of choices.

    Args:
        *valid_values: valid value choices

    Returns:
        parameterized function to validate value choices
    """
    def _choices_inner(value: Any) -> Any:
        if value not in valid_values:
            raise ValueError(f'Value is not one of the choices below: {value}',
                             *valid_values)
    return _choices_inner


def num_limit(minimum: float | None,
              maximum: float | None,
              ) -> ArgumentAdapter:
    """Adapter factory for an input int/float number checked against limits.

    Type inspection for float also accepts an int type.

    This must be called to receive a parameterized function.

    Args:
        minimum: minimum number value
        maximum: maximum number value

    Returns:
        parameterized function to perform checking and conversion
    """
    def _number_range_inner(value: float) -> float:
        if not isinstance(value, (int, float)):
            raise TypeError(f'{value} is not int or float')
        if minimum is not None and value < minimum:
            raise ValueError(f'{value} is less than {minimum}')
        if maximum is not None and value > maximum:
            raise ValueError(f'{value} is greater than {maximum}')
        return value
    return _number_range_inner


def path_exists(value: str | Path) -> str:
    """Adapter that checks if a path exists.

    Args:
        value: file or folder path

    Returns:
        unchanged path
    """
    if not os.path.exists(str(value)):
        raise ValueError(f'path "{value}" does not exist')
    return value


def path_expand_user(value: str | Path) -> str | Path:
    """Adapter that expands a user path, e.g. that starts with "~/".

    Args:
        value: path string

    Returns:
        expanded path string
    """
    if isinstance(value, Path):
        return value.expanduser()
    return os.path.expanduser(value)


def path_expand_environment(value: str | Path) -> str | Path:
    """Adapter that expands a path with environment variables.

    Args:
        value: path string

    Returns:
        expanded path string
    """
    expanded = os.path.expandvars(str(value))
    if isinstance(value, Path):
        expanded = Path(expanded)
    return expanded


def path_is_file(value: str | Path) -> str | Path:
    """Adapter that checks if a path is a file.

    Args:
        value: path string

    Returns:
        unchanged path
    """
    if not os.path.isfile(str(value)):
        raise ValueError(f'"{value}" is not a file')
    return value


def path_is_folder(value: str | Path) -> str | Path:
    """Adapter that checks if a path is a folder.

    Args:
        value: path string

    Returns:
        unchanged path
    """
    if not os.path.isdir(value):
        raise ValueError(f'"{value}" is not a folder')
    return value


def path_to_absolute(value: str | Path) -> str | Path:
    """Adapter that makes a path absolute.

    Args:
        value: path string

    Returns:
        absolute path string
    """
    if isinstance(value, Path):
        return value.absolute()
    return os.path.abspath(value)


def to_age(value: str) -> float:
    """Adapter for age, i.e. negative time delta.

    See util.date_time.parse_date_time_delta() for more information
    about delta strings.

    Args:
        value: time delta string

    Returns:
        timestamp float
    """
    return mktime(apply_date_time_delta_string(value, negative=True))


def to_bool(value: str | bool) -> bool:
    """Convert yes/no/true/false string to bool.

    Args:
        value: input boolean string

    Returns:
        output boolean value
    """
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        raise TypeError(f'not a string')
    lowercase_value = value.lower()
    if lowercase_value in ('yes', 'true'):
        return True
    if lowercase_value in ('no', 'false'):
        return False
    raise ValueError(f'bad boolean string "{value}"')


def to_comma_list(value: str) -> list[str]:
    """Adapter for comma-separated string to list conversion.

    Args:
        value: comma-separated string

    Returns:
        returned string tuple
    """
    return list(value_item.strip() for value_item in value.split(','))


def to_int(value: str, base: int = None) -> int:
    """Convert string to integer.

    Args:
        value: input hex string
        base: optional conversion base (default: 10)

    Returns:
        output integer value
    """
    if base is not None:
        return int(value, base=base)
    return int(value)


def to_float(value: str) -> float:
    """Convert string to float.

    Args:
        value: input hex string

    Returns:
        output float value
    """
    return float(value)


def to_interval(value: str) -> int:
    """Adapter for string to time interval conversion.

    Args:
        value: raw text value

    Returns:
        returned interval integer
    """
    return parse_time_interval(value)


def to_timestamp(value: str) -> float:
    """Adapter for string to timestamp float conversion.

    Args:
        value: date/time string

    Returns:
        timestamp float, as returned by mktime()
    """
    parsed_time_struct = parse_date_time(value)
    if not parsed_time_struct:
        raise ValueError(f'bad date/time string "{value}"')
    return mktime(parsed_time_struct)
