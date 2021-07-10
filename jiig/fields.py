"""
Task field declaration functions.
"""

from typing import Text, Union, List, Type, Collection

from .adapters import to_timestamp, to_interval, to_age, to_comma_tuple, \
    to_int, to_float, to_bool, path_is_folder, path_to_absolute, path_exists
from .registry import Field
from .util.repetition import RepeatSpec

# Returned types need to handle List[...] when repeat is specified.
FIELD_TEXT_TYPE = Type[Union[Text, List[Text]]]
FIELD_BOOL_TYPE = Type[Union[bool, List[bool]]]
FIELD_INT_TYPE = Type[Union[int, List[int]]]
FIELD_FLOAT_TYPE = Type[Union[float, List[float]]]
FIELD_NUMBER_TYPE = Type[Union[Union[int, float], List[Union[int, float]]]]
FIELD_TEXT_LIST_TYPE = Type[Union[List[Text], List[List[Text]]]]


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
    return Field.wrap(Union[float, int],
                      adapters=[to_float],
                      repeat=repeat,
                      choices=choices)


def text(repeat: RepeatSpec = None,
         choices: Collection[Text] = None,
         ) -> FIELD_TEXT_TYPE:
    """
    Declare a text field.

    :param repeat: optional repetition as count or minimum/maximum pair
    :param choices: optional permitted values
    :return: field specification
    """
    return Field.wrap(Text, repeat=repeat, choices=choices)


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
    return Field.wrap(Text, adapters=adapters_list, repeat=repeat)


def filesystem_object(absolute_path: bool = False,
                      exists: bool = False,
                      repeat: RepeatSpec = None,
                      ) -> FIELD_TEXT_TYPE:
    """
    Declare a folder path field.

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
    return Field.wrap(Text, adapters=adapters_list, repeat=repeat)


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


def comma_tuple(repeat: RepeatSpec = None) -> FIELD_TEXT_LIST_TYPE:
    """
    Comma-separated string converted to tuple.

    :param repeat: optional repetition as count or minimum/maximum pair
    :return: field specification
    """
    return Field.wrap(List[Text], adapters=[to_comma_tuple], repeat=repeat)
