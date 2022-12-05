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
General-purpose (independent) utilities.

Make sure that any other utility module can import this module without circular
import references. I.e. DO NOT import other utility modules here.

To handle errors independently, avoid functions like console.log_error(), and
either throw an exception or provide an informative return value.
"""

from dataclasses import dataclass
from typing import Any, Sequence, Callable


class MetaAttrDict(type):
    """
    Meta-class for creating dictionary-based classes with attribute style access.

    This can be used directly for user-created attribute dictionaries, but for
    convenience, all combinations of options are wrapped in canned AttrDict...
    classes below.
    """

    # noinspection PyUnresolvedReferences
    def __new__(mcs, mcs_name, bases, namespace, **kwargs):
        """
        Create a new attribute-dictionary class.

        :param mcs_name: class name
        :param bases: base classes
        :param namespace: class attributes
        :param kwargs: keyword arguments with options from class declaration
        """

        # Safety check that the class inherits from dict.
        if dict not in bases:
            raise TypeError(f'Class {mcs_name} is not based on dict.')

        # Create the class before mixing in attribute access methods below.
        new_class = super(MetaAttrDict, mcs).__new__(mcs, mcs_name, bases, namespace)

        # Attribute read access with no_defaults=True raises AttributeError for non-existent key.
        if kwargs.get('no_defaults', False):
            def getattr_stub(self, name):
                if name not in self:
                    raise AttributeError(f"Attempt to read missing attribute '{name}' in {mcs_name}.")
                return self[name]
            setattr(new_class, '__getattr__', getattr_stub)

        # Attribute read access otherwise uses get() to return value or None.
        else:
            setattr(new_class, '__getattr__', new_class.get)

        # Attribute write access attempt with read_only=True raises AttributeError.
        if kwargs.get('read_only', False):
            # noinspection PyUnusedLocal
            def setattr_stub(self, name, value):
                raise AttributeError(f"Attempt to write to attribute '{name}' in read-only {mcs_name}.")
            setattr(new_class, '__setattr__', setattr_stub)

        # Attribute write access otherwise performs dictionary assignment.
        else:
            setattr(new_class, '__setattr__', new_class.__setitem__)

        return new_class


class AttrDict(dict, metaclass=MetaAttrDict):
    """Dictionary wrapper with attribute-based item access."""
    pass


class AttrDictReadOnly(dict, metaclass=MetaAttrDict, read_only=True):
    """Dictionary wrapper with read-only attribute-based item access."""
    pass


class AttrDictNoDefaults(dict, metaclass=MetaAttrDict, no_defaults=True):
    """
    Dictionary wrapper with attribute-based item access.

    Raises AttributeError when attempting to read a non-existent name.
    """
    pass


class AttrDictNoDefaultsReadOnly(dict, metaclass=MetaAttrDict, no_defaults=True, read_only=True):
    """
    Dictionary wrapper with read-only attribute-based item access.

    Raises AttributeError when attempting to read a non-existent name.
    """
    pass


@dataclass
class DefaultValue:
    value: Any


def make_list(value: Any, strings: bool = False, allow_none: bool = False) -> list | None:
    """
    Coerce a sequence or non-sequence to a list.

    :param value: item to make into a list
    :param strings: convert to text strings if True
    :param allow_none: return None if value is None if True, otherwise empty list
    :return: resulting list or None if value is None
    """
    def _fix(items: list) -> list:
        if not strings:
            return items
        return [str(item) for item in items]
    if value is None:
        return None if allow_none else []
    if isinstance(value, list):
        return _fix(value)
    if isinstance(value, tuple):
        return _fix(list(value))
    return _fix([value])


def make_tuple(value: Any, strings: bool = False, allow_none: bool = False) -> tuple | None:
    """
    Coerce a sequence or non-sequence to a tuple.

    :param value: item to make into a tuple
    :param strings: convert to text strings if True
    :param allow_none: return None if value is None if True, otherwise empty list
    :return: resulting tuple or None if value is None
    """
    def _fix(items: tuple) -> tuple:
        if not strings:
            return items
        return tuple(str(item) for item in items)
    if value is None:
        return None if allow_none else tuple()
    if isinstance(value, tuple):
        return _fix(value)
    if isinstance(value, list):
        return _fix(tuple(value))
    return _fix(tuple([value]))


def make_string(item: Any | None) -> str:
    """
    Coerce any value to a string with None becoming an empty string.

    :param item: item to convert
    :return: converted string
    """
    if item is None:
        return ''
    return str(item)


HUMAN_BINARY_UNITS = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
HUMAN_DECIMAL_UNITS = ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']


def human_byte_count(byte_count: float,
                     unit_format: str | None,
                     ) -> tuple[float, str]:
    """
    Adjust raw byte count to add appropriate unit.

    unit_format values:
      b: binary/1024-based KiB, MiB, etc.
      d: decimal/1000-based KB, MB, etc.
      other: returns error text instead of unit

    :param byte_count: input byte count
    :param unit_format: 'd' for KB/MB/..., 'b' for KiB/MiB/..., or bytes if None
    :return: (adjusted byte count, unit string) tuple
    """
    byte_count = float(byte_count)      # cya
    if unit_format is None:
        return byte_count, ''
    unit_format = unit_format.lower()
    if unit_format not in ['b', 'd']:
        return byte_count, f'(unit format "{unit_format}"?)'
    if unit_format.lower() == 'b':
        divisor = 1024
        unit_strings = HUMAN_BINARY_UNITS
    else:
        divisor = 1000
        unit_strings = HUMAN_DECIMAL_UNITS
    adjusted_quantity = byte_count
    for unit_idx in range(len(unit_strings)):
        if adjusted_quantity < divisor:
            if unit_idx == 0:
                return float(byte_count), ''
            return adjusted_quantity, unit_strings[unit_idx - 1]
        adjusted_quantity /= divisor
    return adjusted_quantity, unit_strings[-1]


def format_human_byte_count(byte_count: int,
                            unit_format: str = None,
                            decimal_places: int = 1
                            ) -> str:
    """
    Format byte count for human consumption using unit abbreviations.

    unit_format values:
      b: binary/1024-based KiB, MiB, etc.
      d: decimal/1000-based KB, MB, etc.
      other: returns error text instead of unit

    :param byte_count: number of bytes
    :param unit_format: 'd' for KB/MB/..., 'b' for KiB/MiB/..., or bytes if None
    :param decimal_places: number of decimal places (default=1 if unit_format specified)
    :return: formatted string with applied unit abbreviation
    """
    return ('{:0.%df}{}' % (decimal_places or 1)).format(
        *human_byte_count(byte_count, unit_format))


def binary_search(sequence: Sequence,
                  value: Any,
                  key: Callable[[Any], Any] = None,
                  ) -> Any | None:
    """
    Perform binary search on ordered sequence.

    Based on standard bisect library, but cloned and adapted code for arbitrary
    item types and an optional key() function. Unlike find(), it returns
    the found item or None, instead of a position or -1.

    :param sequence: ordered item sequence to search
    :param value: value to search for
    :param key: optional key function a la sort() to return item key value
    :return: found item or None if not found
    """
    # "Borrowed" and adapted code from bisect.bisect_left().
    lo = 0
    hi = len(sequence)
    while lo < hi:
        mid = (lo + hi) // 2
        # Use __lt__ to match the logic in list.sort() and in heapq
        item = sequence[mid]
        if key is None:
            key_value = item
        else:
            key_value = key(item)
        if key_value < value:
            lo = mid + 1
        else:
            hi = mid
    if lo == len(sequence):
        return None
    return sequence[lo]


def filter_dict(function: Callable[[Any, Any], bool],
                input_data: dict | Sequence[tuple[Any, Any]],
                ) -> dict:
    """
    Apply filter function to a dictionary or pair sequence.

    :param function: function passed key and value arguments and returns True to keep
    :param input_data: input dictionary or pair sequence
    :return: filtered output dictionary
    """
    # If input data is not a dictionary assume it's a pair sequence.
    return dict(
        filter(
            lambda kv: function(kv[0], kv[1]),
            input_data.items() if isinstance(input_data, dict) else input_data
        )
    )
