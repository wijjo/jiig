"""Driver application data."""

from dataclasses import dataclass
from typing import List, Text

from .driver_task import DriverTask


@dataclass
class DriverInitializationData:
    """Data provided by driver initialization."""
    final_arguments: List[Text]


@dataclass
class DriverApplicationData:
    """Data provided by application initialization."""
    task_stack: List[DriverTask]
    """Task stack."""
    data: object
    """Attributes received from options and arguments."""
