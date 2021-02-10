"""
Task argument data.
"""

from dataclasses import dataclass
from typing import Text, List, Any

from jiig.typing import ArgumentAdapter, Cardinality


@dataclass
class ArgumentData:
    """Command argument."""
    name: Text
    description: Text
    adapters: List[ArgumentAdapter] = None
    cardinality: Cardinality = None
    default_value: Any = None
    choices: List = None
