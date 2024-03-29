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

from typing import (
    Any,
    Callable,
    Self,
    Sequence,
)


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
                class_name: str = None,
                no_defaults: bool = False,
                read_only: bool = False,
                max_depth: int = None,
                ) -> 'MetaAttributeDictionary':
        """Create a new attribute-dictionary class.

        Nested attribute-dictionary instances have a "__key_stack__" attribute
        that allows exception messages to report the full key name.

        Args:
            mcs_name: class name
            bases: base classes
            namespace: class attributes
            class_name: optional class name override
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
        dict_class = super(MetaAttributeDictionary, mcs).__new__(
            mcs, mcs_name, bases, namespace)

        if class_name is None:
            class_name = mcs_name

        def get_full_key_name(dict_instance: dict, key: Any):
            return '.'.join(getattr(dict_instance, '__key_stack__', []) + [key])

        # --- enhanced __getattr__()

        if no_defaults:
            def get_item_function(self, key: Any) -> Any:
                if key not in self:
                    full_name = get_full_key_name(self, key)
                    raise AttributeError(
                        f'{class_name} attribute does not exist: {full_name}')
                return self[key]
        else:
            # noinspection PyUnresolvedReferences
            get_item_function = dict_class.get

        if max_depth != 1:
            def get_attribute_function(self, name: Any) -> Any:
                if name == '__key_stack__':
                    return super(dict, self).__getattr__(name)

                def wrap_value_recursive(value: Any, depth: int = 0) -> Any:
                    if max_depth is None or depth < max_depth:
                        if isinstance(value, dict):
                            sub_dict = dict_class(value)
                            parent_key_stack = getattr(value, '__key_stack__', [])
                            setattr(sub_dict, '__key_stack__', parent_key_stack + [name])
                            return sub_dict
                        if isinstance(value, list):
                            return [wrap_value_recursive(sub_value, depth=depth + 1)
                                    for sub_value in value]
                        if isinstance(value, tuple):
                            return tuple(wrap_value_recursive(sub_value, depth=depth + 1)
                                         for sub_value in value)
                    return value

                return wrap_value_recursive(get_item_function(self, name))
        else:
            get_attribute_function = get_item_function
        setattr(dict_class, '__getattr__', get_attribute_function)

        # --- enhanced __setattr__()

        if read_only:
            # Read-only attribute write raises AttributeError.

            def set_attribute_function(self, name, value):
                # Reject attribute write, except for special key stack one.
                if name == '__key_stack__':
                    super(dict, self).__setattr__(name, value)
                    return
                full_name = get_full_key_name(self, name)
                raise AttributeError(
                    f'{class_name} attribute may not be  set: {full_name}')

        else:
            # Non-read-only attribute write performs dictionary assignment.
            # noinspection PyUnresolvedReferences
            set_attribute_function = dict_class.__setitem__
        setattr(dict_class, '__setattr__', set_attribute_function)

        return dict_class


class AttributeDictionary(dict):
    """Placeholder class for new() return."""

    def __getattr__(self, key: Any) -> Any:
        raise NotImplementedError(f'Create {self.__class__.__name__} with new().')

    def __setattr__(self, key: Any, value: Any):
        raise NotImplementedError(f'Create {self.__class__.__name__} with new().')

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
                                        class_name=cls.__name__,
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
