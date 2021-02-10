"""
Task option data.
"""

from dataclasses import dataclass
from typing import Text, List, Any

from jiig.typing import OptionFlag, ArgumentAdapter, Cardinality


@dataclass
class OptionData:
    """Command option."""
    name: Text
    flags: List[OptionFlag]
    description: Text
    adapters: List[ArgumentAdapter] = None
    cardinality: Cardinality = None
    default_value: Any = None
    choices: List = None
    is_boolean: bool = False

