"""
Registered option argument data.
"""

from dataclasses import dataclass
from typing import Text, List, Any, Sequence

from jiig.typing import ArgumentAdapter, Cardinality, OptionFlag


@dataclass
class RegisteredOption:
    """Registered option data."""
    name: Text
    flags: List[OptionFlag]
    description: Text
    adapters: List[ArgumentAdapter] = None
    cardinality: Cardinality = None
    default_value: Any = None
    choices: Sequence = None
    is_boolean: bool = False
