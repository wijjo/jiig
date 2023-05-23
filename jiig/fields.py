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

"""Task field declaration functions.

Jiig task fields substitute for Python type hints to specify the type, but also
to add validation and conversion.
"""

from typing import (
    Annotated,
    Any,
    Collection,
)

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
from .types import (
    ArgumentAdapter,
    Field,
)
from .util.collections import make_list
from .util.repetition import (
    RepeatSpec,
    repetition_from_spec,
)

# Returned types need to handle List[...] when repeat is specified.
FIELD_TEXT_TYPE = type[str | list[str]]
FIELD_BOOL_TYPE = type[bool | list[bool]]
FIELD_INT_TYPE = type[int | list[int]]
FIELD_FLOAT_TYPE = type[float | list[float]]
FIELD_NUMBER_TYPE = type[int | float | list[int | float]]
FIELD_TEXT_LIST_TYPE = type[list[str] | list[list[str]]]


def wrap_field(element_type: Any,
               description: str = None,
               field_type: Any = None,
               adapters: Collection[ArgumentAdapter] = None,
               repeat: RepeatSpec = None,
               choices: Collection = None,
               ) -> Any:
    """Create Field and wrap in Annotated hint.

    Args:
        element_type: scalar element type
        description: field description
        field_type: field type (defaults to element_type if missing)
        adapters: field adapter function chain
        repeat: optional repeat specification as count or minimum/maximum pair
        choices: optional value choices
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
    """Declare an integer numeric field.

    Args:
        repeat: optional repetition as count or minimum/maximum pair
        choices: optional permitted values

    Returns:
        field specification
    """
    return wrap_field(int, adapters=[to_int], repeat=repeat, choices=choices)


def number(repeat: RepeatSpec = None,
           choices: Collection[int] = None,
           ) -> FIELD_NUMBER_TYPE:
    """Declare a float or integer numeric field.

    Args:
        repeat: optional repetition as count or minimum/maximum pair
        choices: optional permitted values

    Returns:
        field specification
    """
    return wrap_field(float | int, adapters=[to_float], repeat=repeat, choices=choices)


def text(repeat: RepeatSpec = None,
         choices: Collection[str] = None,
         ) -> FIELD_TEXT_TYPE:
    """Declare a text field.

    Args:
        repeat: optional repetition as count or minimum/maximum pair
        choices: optional permitted values

    Returns:
        field specification
    """
    return wrap_field(str, repeat=repeat, choices=choices)


def boolean(repeat: RepeatSpec = None) -> FIELD_BOOL_TYPE:
    """Declare a boolean field.

    Args:
        repeat: optional repetition as count or minimum/maximum pair

    Returns:
        field specification
    """
    return wrap_field(bool, adapters=[to_bool], repeat=repeat)


def filesystem_folder(absolute_path: bool = False,
                      repeat: RepeatSpec = None,
                      ) -> FIELD_TEXT_TYPE:
    """Declare a folder path field.

    Args:
        absolute_path: convert to absolute path if True
        repeat: optional repetition as count or minimum/maximum pair

    Returns:
        field specification
    """
    adapters_list = [path_is_folder]
    if absolute_path:
        adapters_list.append(path_to_absolute)
    return wrap_field(str, adapters=adapters_list, repeat=repeat)


def filesystem_file(absolute_path: bool = False,
                    repeat: RepeatSpec = None,
                    ) -> FIELD_TEXT_TYPE:
    """Declare a folder path field.

    Args:
        absolute_path: convert to absolute path if True
        repeat: optional repetition as count or minimum/maximum pair

    Returns:
        field specification
    """
    adapters_list = [path_is_file]
    if absolute_path:
        adapters_list.append(path_to_absolute)
    return wrap_field(str, adapters=adapters_list, repeat=repeat)


def filesystem_object(absolute_path: bool = False,
                      exists: bool = False,
                      repeat: RepeatSpec = None,
                      ) -> FIELD_TEXT_TYPE:
    """Declare a file or folder path field.

    Args:
        absolute_path: convert to absolute path if True
        exists: it must exist if True
        repeat: optional repetition as count or minimum/maximum pair

    Returns:
        field specification
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
    """Age based on string specification.

    See util.date_time.parse_date_time_delta() for more information about age strings.

    Args:
        repeat: optional repetition as count or minimum/maximum pair
        choices: optional permitted values

    Returns:
        field specification
    """
    return wrap_field(float, adapters=[to_age], repeat=repeat, choices=choices)


def timestamp(repeat: RepeatSpec = None) -> FIELD_FLOAT_TYPE:
    """Timestamp based on string specification.

    Args:
        repeat: optional repetition as count or minimum/maximum pair

    Returns:
        field specification
    """
    return wrap_field(float, adapters=[to_timestamp], repeat=repeat)


def interval(repeat: RepeatSpec = None,
             choices: Collection[int] = None,
             ) -> FIELD_FLOAT_TYPE:
    """Time interval based on string specification.

    Args:
        repeat: optional repetition as count or minimum/maximum pair
        choices: optional permitted values

    Returns:
        field specification
    """
    return wrap_field(float, adapters=[to_interval], repeat=repeat, choices=choices)


def comma_list(repeat: RepeatSpec = None) -> FIELD_TEXT_LIST_TYPE:
    """Comma-separated string converted to list.

    Args:
        repeat: optional repetition as count or minimum/maximum pair

    Returns:
        field specification
    """
    return wrap_field(list[str], adapters=[to_comma_list], repeat=repeat)
