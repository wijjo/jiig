"""
Jiig text adapter functions.
"""

from typing import Text, Tuple


def comma_tuple(value: str) -> Tuple[Text]:
    """
    Adapter for comma-separated string to tuple conversion.

    :param value: comma-separated string
    :return: returned string tuple
    """
    return tuple(tag.strip() for tag in value.split(','))
