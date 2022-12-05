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
Task field declaration functions.
"""

from typing import Type, Collection

from .adapters import to_timestamp, to_interval, to_age, to_comma_list, \
    to_int, to_float, to_bool, path_is_folder, path_to_absolute, path_exists, path_is_file
from .registry import Field
from .util.repetition import RepeatSpec

# Returned types need to handle List[...] when repeat is specified.
FIELD_TEXT_TYPE = Type[str | list[str]]
FIELD_BOOL_TYPE = Type[bool | list[bool]]
FIELD_INT_TYPE = Type[int | list[int]]
FIELD_FLOAT_TYPE = Type[float | list[float]]
FIELD_NUMBER_TYPE = Type[int | float | list[int | float]]
FIELD_TEXT_LIST_TYPE = Type[list[str] | list[list[str]]]


def integer(repeat: RepeatSpec = None,
            choices: Collection[int] = None,
            ) -> FIELD_INT_TYPE:
    """
    Declare an integer numeric field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return Field.wrap(int, adapters=[to_int], repeat=repeat, choices=choices)


def number(repeat: RepeatSpec = None,
           choices: Collection[int] = None,
           ) -> FIELD_NUMBER_TYPE:
    """
    Declare a float or integer numeric field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return Field.wrap(float | int,
                      adapters=[to_float],
                      repeat=repeat,
                      choices=choices)


def text(repeat: RepeatSpec = None,
         choices: Collection[str] = None,
         ) -> FIELD_TEXT_TYPE:
    """
    Declare a text field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return Field.wrap(str, repeat=repeat, choices=choices)


def boolean(repeat: RepeatSpec = None) -> FIELD_BOOL_TYPE:
    """
    Declare a boolean field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    return Field.wrap(bool, adapters=[to_bool], repeat=repeat)


def filesystem_folder(absolute_path: bool = False,
                      repeat: RepeatSpec = None,
                      ) -> FIELD_TEXT_TYPE:
    """
    Declare a folder path field.

    :param absolute_path: convert to absolute path if True
    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    adapters_list = [path_is_folder]
    if absolute_path:
        adapters_list.append(path_to_absolute)
    return Field.wrap(str, adapters=adapters_list, repeat=repeat)


def filesystem_file(absolute_path: bool = False,
                    repeat: RepeatSpec = None,
                    ) -> FIELD_TEXT_TYPE:
    """
    Declare a folder path field.

    :param absolute_path: convert to absolute path if True
    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    adapters_list = [path_is_file]
    if absolute_path:
        adapters_list.append(path_to_absolute)
    return Field.wrap(str, adapters=adapters_list, repeat=repeat)


def filesystem_object(absolute_path: bool = False,
                      exists: bool = False,
                      repeat: RepeatSpec = None,
                      ) -> FIELD_TEXT_TYPE:
    """
    Declare a file or folder path field.

    :param absolute_path: convert to absolute path if True
    :param exists: it must exist if True
    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    adapters_list = []
    if absolute_path:
        adapters_list.append(path_to_absolute)
    if exists:
        adapters_list.append(path_exists)
    return Field.wrap(str, adapters=adapters_list, repeat=repeat)


def age(repeat: RepeatSpec = None,
        choices: Collection[int] = None,
        ) -> FIELD_FLOAT_TYPE:
    """
    Age based on string specification.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return Field.wrap(float, adapters=[to_age], repeat=repeat, choices=choices)


def timestamp(repeat: RepeatSpec = None) -> FIELD_FLOAT_TYPE:
    """
    Timestamp based on string specification.

    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    return Field.wrap(float, adapters=[to_timestamp], repeat=repeat)


def interval(repeat: RepeatSpec = None,
             choices: Collection[int] = None,
             ) -> FIELD_FLOAT_TYPE:
    """
    Time interval based on string specification.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return Field.wrap(float, adapters=[to_interval], repeat=repeat, choices=choices)


def comma_list(repeat: RepeatSpec = None) -> FIELD_TEXT_LIST_TYPE:
    """
    Comma-separated string converted to list.

    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    return Field.wrap(list[str], adapters=[to_comma_list], repeat=repeat)
