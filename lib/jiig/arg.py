"""
Jiig argument adapters, converters, etc..
"""

import base64
import binascii
import os
from time import mktime
from typing import Text, Any, Optional, Tuple

from jiig.util.date_time import parse_date_time, parse_time_interval, \
    apply_date_time_delta_string

from .typing import ArgumentAdapter


class Choices:
    """Added to provide a choices list to an argument definition."""
    def __init__(self, *values: Any):
        if not values:
            raise ValueError('choices() was not passed any values')
        self.values = values


class Default:
    """Used to add a default value to an argument definition tuple."""
    def __init__(self, value: Any):
        self.value = value


def b64_decode(value: str) -> str:
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


def b64_encode(value: str) -> str:
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


def choices(*values: Any) -> Choices:
    """
    Add choices list to an argument definition.
    :param values: valid value choices
    :return: Choices object
    """
    return Choices(*values)


def default(value: Any) -> Default:
    """
    Add default value to an argument definition.
    :param value: default value
    :return: Default object
    """
    return Default(value)


def num_limit(minimum: Optional[float], maximum: Optional[float]) -> ArgumentAdapter:
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


def path_exists(value: str) -> str:
    """
    Adapter that checks if a path exists.

    :param value: file or folder path
    :return: unchanged path
    """
    if not os.path.exists(value):
        raise ValueError('path does not exist')
    return value


def path_expand_user(value: str) -> str:
    """
    Adapter that expands a user path, e.g. that starts with "~/".

    :param value: path string
    :return: expanded path string
    """
    return os.path.expanduser(value)


def path_expand_environment(value: str) -> str:
    """
    Adapter that expands a path with environment variables.

    :param value: path string
    :return: expanded path string
    """
    return os.path.expandvars(value)


def path_is_file(value: str) -> str:
    """
    Adapter that checks if a path is a file.

    :param value: path string
    :return: unchanged path
    """
    if not os.path.isfile(value):
        raise ValueError('path is not a file')
    return value


def path_is_folder(value: str) -> str:
    """
    Adapter that checks if a path is a folder.

    :param value: path string
    :return: unchanged path
    """
    if not os.path.isdir(value):
        raise ValueError('path is not a folder')
    return value


def path_to_absolute(value: str) -> str:
    """
    Adapter that makes a path absolute.

    :param value: path string
    :return: absolute path string
    """
    return os.path.abspath(value)


def str_to_age(value: str) -> float:
    """
    Adapter for age, i.e. negative time delta.

    See jiig.utility.date_time.parse_date_time_delta() for more information
    about delta strings.

    :param value: time delta string
    :return: timestamp float
    """
    return mktime(apply_date_time_delta_string(value, negative=True))


def str_to_bool(value: str) -> bool:
    """
    Convert yes/no/true/false string to bool.

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


def str_to_comma_tuple(value: str) -> Tuple[Text]:
    """
    Adapter for comma-separated string to tuple conversion.

    :param value: comma-separated string
    :return: returned string tuple
    """
    return tuple(tag.strip() for tag in value.split(','))


def str_to_int(value: str, base: int = 10) -> int:
    """
    Convert string to integer.

    :param value: input hex string
    :param base: conversion base (default: 10)
    :return: output integer value
    """
    return int(value, base=base)


def str_to_float(value: str) -> float:
    """
    Convert string to float.

    :param value: input hex string
    :return: output float value
    """
    return float(value)


def str_to_interval(value: str) -> int:
    """
    Adapter for string to time interval conversion.

    :param value: raw text value
    :return: returned interval integer
    """
    return parse_time_interval(value)


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
