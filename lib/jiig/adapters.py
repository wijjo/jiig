"""
Jiig argument adapters.

Simple functions that can be used as adapters in argument declarations.

Note that built-in Python types, e.g. bool, int, and float, may be used
directly in adapter chains. They serve the dual purpose of declaring the output
type and, in some cases, converting input strings.

Also note that `bool` has a special meaning for option arguments. Using `bool`
as the adapter is the only way to declare a boolean flag option that does not
take a value argument.
"""

import base64
import binascii
import os
from time import mktime
from typing import Optional

from jiig.tool_registry import ArgumentAdapter
from jiig.utility.date_time import parse_date_time, parse_time_interval


def str_to_bool(value: str) -> bool:
    """
    Boolean adapter to convert yes/no/true/false strings to a bool.

    :param value: input boolean string
    :return: output boolean value
    """
    if not isinstance(value, str):
        raise TypeError(f'not a string')
    lowercase_value = value.lower()
    if lowercase_value in ('yes', 'true'):
        return True
    if lowercase_value in ('no', 'false'):
        return False
    raise ValueError(f'bad boolean string')


def hex_str_to_int(value: str) -> int:
    """
    Convert hex string to integer.

    :param value: input hex string
    :return: output integer value
    """
    return int(value, 16)


def octal_str_to_int(value: str) -> int:
    """
    Convert octal string to integer.

    :param value: input octal string
    :return: output integer value
    """
    return int(value, 8)


def binary_str_to_int(value: str) -> int:
    """
    Convert binary string to integer.

    :param value: input binary string
    :return: output integer value
    """
    return int(value, 2)


def base64_decode(value: str) -> str:
    """
    Decode base64 string.

    :param value: input base64 string
    :return: output utf-8 string
    """
    try:
        return base64.standard_b64decode(value).decode('utf-8')
    except binascii.Error as exc:
        # Wrap as ValueError, because binascii.Error will not be caught for the argument.
        raise ValueError(str(exc))


def base64_encode(value: str) -> str:
    """
    Encode string to base64.

    :param value: input string
    :return: output base64 string
    """
    try:
        return base64.standard_b64encode(bytes(value, 'utf-8')).decode('utf-8')
    except binascii.Error as exc:
        # Wrap as ValueError, because binascii.Error will not be caught for the argument.
        raise ValueError(str(exc))


def number_range(minimum: Optional[float], maximum: Optional[float]) -> ArgumentAdapter:
    """
    Adapter factory for an input int/float number checked against limits.

    Type inspection for float also accepts an int type.

    This must be called to receive a parameterized function.

    :param minimum: minimum number value
    :param maximum: maximum number value
    :return: parameterized function to perform checking and conversion
    """
    def _number_range_inner(value: float) -> float:
        if not isinstance(value, (int, float)):
            raise TypeError('not int/float')
        if minimum is not None and value < minimum:
            raise ValueError(f'less than {minimum}')
        if maximum is not None and value > maximum:
            raise ValueError(f'more than {maximum}')
        return value
    return _number_range_inner


def str_to_timestamp(value: str) -> float:
    """
    Adapter for string to timestamp float conversion.

    :param value: date/time string
    :return: timestamp float, as returned by mktime()
    """
    parsed_time_struct = parse_date_time(value)
    if not parsed_time_struct:
        raise ValueError('bad date/time string')
    return mktime(parsed_time_struct)


def str_to_interval(value: str) -> int:
    """
    Adapter for string to time interval conversion.

    :param value: raw text value
    :return: returned interval integer
    """
    return parse_time_interval(value)


def existing_path(value: str) -> str:
    """
    Adapter that checks if a path exists.

    :param value: file or folder path
    :return: unchanged path
    """
    if not os.path.exists(value):
        raise ValueError('path does not exist')
    return value


def folder_path(value: str) -> str:
    """
    Adapter that checks if a path is a folder.

    :param value: path string
    :return: unchanged path
    """
    if not os.path.isdir(value):
        raise ValueError('path is not a folder')
    return value


def file_path(value: str) -> str:
    """
    Adapter that checks if a path is a file.

    :param value: path string
    :return: unchanged path
    """
    if not os.path.isfile(value):
        raise ValueError('path is not a file')
    return value


def user_path(value: str) -> str:
    """
    Adapter that expands a user path, e.g. that starts with "~/".

    :param value: path string
    :return: expanded path string
    """
    return os.path.expanduser(value)


def environment_path(value: str) -> str:
    """
    Adapter that expands a path with environment variables.

    :param value: path string
    :return: expanded path string
    """
    return os.path.expandvars(value)


def absolute_path(value: str) -> str:
    """
    Adapter that makes a path absolute.

    :param value: path string
    :return: absolute path string
    """
    return os.path.abspath(value)
