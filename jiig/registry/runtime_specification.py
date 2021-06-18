"""
Runtime specification that eventually feeds into a Runtime instance.
"""

from dataclasses import dataclass
from typing import Type, Text, Union

# Reference to registered Runtime class, module name, or loaded module, with
# `object` representing loaded module, due to lack of better alternative.
RuntimeReference = Union[Type, Text, object]


@dataclass
class RuntimeSpecification:
    """
    Registered Runtime specification.

    Not user-created. Constructed for registered Runtime classes.
    """

    runtime_class: Type
    """Runtime class to be constructed with appropriate data."""
