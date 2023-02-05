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
Task field declaration functions.
"""

from dataclasses import dataclass
from typing import Type, Collection, Any, Annotated

from .adapters import (
    path_exists,
    path_is_file,
    path_is_folder,
    path_to_absolute,
    to_age,
    to_bool,
    to_comma_list,
    to_float,
    to_int,
    to_interval,
    to_timestamp,
)
from .types import ArgumentAdapter
from .util.collections import make_list
from .util.default import DefaultValue
from .util.repetition import Repetition, repetition_from_spec
from .util.types import RepeatSpec

# Returned types need to handle List[...] when repeat is specified.
FIELD_TEXT_TYPE = Type[str | list[str]]
FIELD_BOOL_TYPE = Type[bool | list[bool]]
FIELD_INT_TYPE = Type[int | list[int]]
FIELD_FLOAT_TYPE = Type[float | list[float]]
FIELD_NUMBER_TYPE = Type[int | float | list[int | float]]
FIELD_TEXT_LIST_TYPE = Type[list[str] | list[list[str]]]


@dataclass
class Field:
    """
    Field specification derived from type annotation.

    Use wrap_field(), instead of creating directly.
    """
    element_type: Any
    """scalar element type"""
    description: str
    """field description"""
    field_type: Any
    """field type (defaults to element_type if missing)"""
    adapters: list[ArgumentAdapter] | None
    """optional field adapter function chain"""
    repeat: Repetition | None
    """optional field repetition data"""
    choices: list | None
    """optional value choices"""


@dataclass
class TaskField:
    """Data extracted from task dataclass or task function signature."""
    name: str
    description: str
    element_type: Any
    field_type: Any
    default: DefaultValue | None
    repeat: Repetition | None
    choices: list | None
    adapters: list[ArgumentAdapter]


def wrap_field(element_type: Any,
               description: str = None,
               field_type: Any = None,
               adapters: Collection[ArgumentAdapter] = None,
               repeat: RepeatSpec = None,
               choices: Collection = None,
               ) -> Any:
    """
    Create Field and wrap in Annotated hint.

    :param element_type: scalar element type
    :param description: field description
    :param field_type: field type (defaults to element_type if missing)
    :param adapters: field adapter function chain
    :param repeat: optional repeat specification as count or minimum/maximum pair
    :param choices: optional value choices
    """
    field = Field(element_type,
                  description=description or '(no field description)',
                  field_type=field_type if field_type is not None else element_type,
                  adapters=make_list(adapters, allow_none=True),
                  repeat=repetition_from_spec(repeat) if repeat is not None else None,
                  choices=make_list(choices, allow_none=True))
    return Annotated[field.field_type, field]


def integer(repeat: RepeatSpec = None,
            choices: Collection[int] = None,
            ) -> FIELD_INT_TYPE:
    """
    Declare an integer numeric field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return wrap_field(int, adapters=[to_int], repeat=repeat, choices=choices)


def number(repeat: RepeatSpec = None,
           choices: Collection[int] = None,
           ) -> FIELD_NUMBER_TYPE:
    """
    Declare a float or integer numeric field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return wrap_field(float | int, adapters=[to_float], repeat=repeat, choices=choices)


def text(repeat: RepeatSpec = None,
         choices: Collection[str] = None,
         ) -> FIELD_TEXT_TYPE:
    """
    Declare a text field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return wrap_field(str, repeat=repeat, choices=choices)


def boolean(repeat: RepeatSpec = None) -> FIELD_BOOL_TYPE:
    """
    Declare a boolean field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    return wrap_field(bool, adapters=[to_bool], repeat=repeat)


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
    return wrap_field(str, adapters=adapters_list, repeat=repeat)


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
    return wrap_field(str, adapters=adapters_list, repeat=repeat)


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
    return wrap_field(str, adapters=adapters_list, repeat=repeat)


def age(repeat: RepeatSpec = None,
        choices: Collection[int] = None,
        ) -> FIELD_FLOAT_TYPE:
    """
    Age based on string specification.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return wrap_field(float, adapters=[to_age], repeat=repeat, choices=choices)


def timestamp(repeat: RepeatSpec = None) -> FIELD_FLOAT_TYPE:
    """
    Timestamp based on string specification.

    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    return wrap_field(float, adapters=[to_timestamp], repeat=repeat)


def interval(repeat: RepeatSpec = None,
             choices: Collection[int] = None,
             ) -> FIELD_FLOAT_TYPE:
    """
    Time interval based on string specification.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return wrap_field(float, adapters=[to_interval], repeat=repeat, choices=choices)


def comma_list(repeat: RepeatSpec = None) -> FIELD_TEXT_LIST_TYPE:
    """
    Comma-separated string converted to list.

    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    return wrap_field(list[str], adapters=[to_comma_list], repeat=repeat)
