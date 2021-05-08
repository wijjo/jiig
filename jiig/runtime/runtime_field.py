"""
Post-registration field data.
"""

from dataclasses import dataclass
from typing import Any, Text, List, Optional, Collection, Dict

from jiig.registry import ArgumentAdapter
from jiig.util.repetition import Repetition


@dataclass
class RuntimeField:
    """Post-registration field data."""
    element_type: Any
    field_type: Any
    description: Text
    default: Any
    adapters: List[ArgumentAdapter]
    repeat: Optional[Repetition]
    choices: Optional[Collection]
    hints: Dict
