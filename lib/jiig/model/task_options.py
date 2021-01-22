"""
Task options.
"""

from dataclasses import dataclass, field
from typing import Text, List


@dataclass
class TaskOptions:
    pip_packages: List[Text] = field(default_factory=list)
    """Pip-installed packages required from a virtual environment, if enabled."""

    receive_trailing_arguments: bool = False
    """Keep unparsed trailing arguments if True."""
