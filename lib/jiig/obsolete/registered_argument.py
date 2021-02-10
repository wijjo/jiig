"""
Registered argument data.
"""

from dataclasses import dataclass
from typing import Text, List, Any, Sequence

from jiig.typing import ArgumentAdapter, Cardinality
z

@dataclass
class RegisteredArgument:
    """Registered argument data."""
    name: Text
    description: Text
    adapters: List[ArgumentAdapter] = None
    cardinality: Cardinality = None
    default_value: Any = None
    choices: Sequence = None
