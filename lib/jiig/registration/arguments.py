"""
Registered task argument dataclass.
"""

from typing import Text, Any, Union, Callable

ArgumentAdapter = Callable[..., Any]
Cardinality = Union[Text, int]
OptionFlag = Text


class Choices:
    """Used to add a choices list to an argument definition tuple."""
    def __init__(self, *values: Any):
        if not values:
            raise ValueError('choices() was not passed any values')
        self.values = values


class Default:
    """Used to add a default value to an argument definition tuple."""
    def __init__(self, value: Any):
        self.value = value
