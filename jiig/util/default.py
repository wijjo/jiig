"""Default value wrapper."""

from dataclasses import dataclass
from typing import Any


@dataclass
class DefaultValue:
    """Default value wrapper to give it a type."""
    value: Any
