"""
Task field functions and classes.
"""

from typing import Text, Annotated, Union, Callable, Protocol

from .adapters import path_is_folder, path_to_absolute

from .registry.field import Field


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
    return Field(int, description, hints)


@field_function
def number(description: Text, **hints) -> Field:
    """
    Declare a float or integer numeric field.

    :param description: field description
    :param hints: driver hints
    :return: field specification
    """
    return Field(Union[float, int], description, hints)


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
    return Field(bool, description, hints)


@field_function
def filesystem_folder(description: Text,
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
    adapters = [path_is_folder]
    if absolute_path:
        adapters.append(path_to_absolute)
    return Field(Text, description, hints, adapters=adapters)
