"""
Task field functions and classes.
"""

from typing import Text, Annotated, Union, Callable, Protocol, List

from .adapters import to_timestamp, to_interval, to_age, to_comma_tuple, \
    to_int, to_float, to_bool, path_is_folder, path_to_absolute, path_exists
from .registry import Field


# === Field declaration functions.


def field_function(function: Callable[..., Field]) -> Callable:
    """
    Decorator for custom field declaration functions.

    Use naked, i.e. without calling.

    Provides the requisite Annotated type wrapped around a FieldSpecification.
    """
    def inner(*args, **kwargs) -> object:
        field_spec = function(*args, **kwargs)
        return Annotated[field_spec.field_type, field_spec]
    return inner


class FieldWrapperCallable(Protocol):
    """Field wrapper type hint that receive a specification plus variable arguments."""
    def __call__(self, spec: Field, *args, **kwargs) -> Field: ...


@field_function
def integer(description: Text, **hints) -> Field:
    """
    Declare an integer numeric field.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(int, description, hints, adapters=[to_int])


@field_function
def number(description: Text, **hints) -> Field:
    """
    Declare a float or integer numeric field.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(Union[float, int], description, hints, adapters=[to_float])


@field_function
def text(description: Text, **hints) -> Field:
    """
    Declare a text field.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(Text, description, hints)


@field_function
def boolean(description: Text, **hints) -> Field:
    """
    Declare a boolean field.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(bool, description, hints, adapters=[to_bool])


@field_function
def filesystem_folder(description: Text, /,
                      absolute_path: bool = False,
                      **hints,
                      ) -> Field:
    """
    Declare a folder path field.

    :param description: field description
    :param absolute_path: convert to absolute path if True
    :param hints: driver hints
    :return: field specification
    """
    adapters_list = [path_is_folder]
    if absolute_path:
        adapters_list.append(path_to_absolute)
    return Field(Text, description, hints, adapters=adapters_list)


@field_function
def filesystem_object(description: Text, /,
                      absolute_path: bool = False,
                      exists: bool = False,
                      **hints,
                      ) -> Field:
    """
    Declare a folder path field.

    :param description: field description
    :param absolute_path: convert to absolute path if True
    :param exists: it must exist if True
    :param hints: driver hints
    :return: field specification
    """
    adapters_list = []
    if absolute_path:
        adapters_list.append(path_to_absolute)
    if exists:
        adapters_list.append(path_exists)
    return Field(Text, description, hints, adapters=adapters_list)


@field_function
def age(description: Text, **hints) -> Field:
    """
    Age based on string specification.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(float, description, hints, adapters=[to_age])


@field_function
def timestamp(description: Text, **hints) -> Field:
    """
    Timestamp based on string specification.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(float, description, hints, adapters=[to_timestamp])


@field_function
def interval(description: Text, **hints) -> Field:
    """
    Time interval based on string specification.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(float, description, hints, adapters=[to_interval])


@field_function
def comma_tuple(description: Text, **hints) -> Field:
    """
    Comma-separated string converted to tuple.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(List[Text], description, hints, adapters=[to_comma_tuple])
