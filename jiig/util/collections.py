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

"""Attribute dictionary meta-classes, classes, and functions."""

from typing import Any, Callable, Sequence, Self


def make_list(value: Any,
              strings: bool = False,
              allow_none: bool = False,
              sep: str = None,
              ) -> list | None:
    """Coerce a sequence or non-sequence to a list.

    Args:
        value: item to make into a list
        strings: convert to text strings if True
        allow_none: return None if value is None if True, otherwise empty list
        sep: split string value using this separator if not None

    Returns:
        resulting list or None if value is None
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
    if sep and isinstance(value, str):
        return value.split(sep)
    return _fix([value])


def make_tuple(value: Any,
               strings: bool = False,
               allow_none: bool = False,
               ) -> tuple | None:
    """Coerce a sequence or non-sequence to a tuple.

    Args:
        value: item to make into a tuple
        strings: convert to text strings if True
        allow_none: return None if value is None if True, otherwise empty list

    Returns:
        resulting tuple or None if value is None
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


class MetaAttributeDictionary(type):
    """Meta-class for creating dict-based classes with attribute style access."""

    def __new__(mcs,
                mcs_name: str,
                bases: tuple[type],
                namespace: [str, Any],
                no_defaults: bool = False,
                read_only: bool = False,
                max_depth: int = None,
                ):
        """Create a new attribute-dictionary class.

        Args:
            mcs_name: class name
            bases: base classes
            namespace: class attributes
            no_defaults: raise AttributeError for missing keys if True
            read_only: disable write access if True
            max_depth: maximum depth for wrapping sub-dictionaries (default: no
                limit)
        """

        # Safety check that the class inherits from dict.
        for base in bases:
            if issubclass(base, dict):
                break
        else:
            raise TypeError(f'Class {mcs_name} is not based on dict.')

        # Create the class before mixing in attribute access methods below.
        new_class = super(MetaAttributeDictionary, mcs).__new__(mcs, mcs_name, bases, namespace)

        # --- __getattr__()

        if no_defaults:
            def get_item_function(self, key: Any) -> Any:
                if key not in self:
                    raise AttributeError(f"Attempt to read missing attribute"
                                         f" '{key}' in {mcs_name}.")
                return self[key]
        else:
            # noinspection PyUnresolvedReferences
            get_item_function = new_class.get

        if max_depth != 1:
            def get_function(self, key: Any) -> Any:
                def wrap_value_recursive(value: Any, depth: int = 0) -> Any:
                    if max_depth is None or depth < max_depth:
                        if isinstance(value, dict):
                            return new_class(value)
                        if isinstance(value, list):
                            return [wrap_value_recursive(sub_value, depth=depth + 1)
                                    for sub_value in value]
                        if isinstance(value, tuple):
                            return tuple(wrap_value_recursive(sub_value, depth=depth + 1)
                                         for sub_value in value)
                    return value
                return wrap_value_recursive(get_item_function(self, key))
        else:
            get_function = get_item_function
        setattr(new_class, '__getattr__', get_function)

        # --- __setattr__()

        # Attribute write access attempt with read_only=True raises AttributeError.
        if read_only:
            # noinspection PyUnusedLocal
            def setattr_stub(self, name, value):
                raise AttributeError(f"Attempt to write to attribute '{name}' in read-only {mcs_name}.")
            setattr(new_class, '__setattr__', setattr_stub)

        # Attribute write access otherwise performs dictionary assignment.
        else:
            # noinspection PyUnresolvedReferences
            setattr(new_class, '__setattr__', new_class.__setitem__)

        return new_class


class AttributeDictionary(dict):
    """Abstract placeholder class for new() return."""

    def __getattr__(self, key: Any) -> Any:
        ...

    def __setattr__(self, key: Any, value: Any):
        ...

    @classmethod
    def new(cls,
            symbols: dict = None,
            no_defaults: bool = False,
            read_only: bool = False,
            max_depth: int = None,
            ) -> Self:
        """Create and initialize a custom dictionary with attribute-based item access.

        Args:
            symbols: optional initial symbols
            no_defaults: raise AttributeError for missing keys if True
            read_only: disable write access if True
            max_depth: maximum depth for wrapping sub-dictionaries (default: no
                limit)

        Returns:
            attribute-based dictionary
        """
        class CustomAttributeDictionary(cls,
                                        metaclass=MetaAttributeDictionary,
                                        no_defaults=no_defaults,
                                        read_only=read_only,
                                        max_depth=max_depth,
                                        ):
            pass

        return CustomAttributeDictionary(symbols or {})


def filter_dict(function: Callable[[Any, Any], bool],
                input_data: dict | Sequence[tuple[Any, Any]],
                ) -> dict:
    """Apply filter function to a dictionary or pair sequence.

    Args:
        function: function passed key and value arguments and returns True to
            keep
        input_data: input dictionary or pair sequence

    Returns:
        filtered output dictionary
    """
    # If input data is not a dictionary assume it's a pair sequence.
    return dict(
        filter(
            lambda kv: function(kv[0], kv[1]),
            input_data.items() if isinstance(input_data, dict) else input_data
        )
    )
