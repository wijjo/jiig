"""Driver options data class."""

from dataclasses import dataclass, field
from typing import Text, List


@dataclass
class DriverOptions:
    """Options governing Jiig driver behavior."""
    variant: Text = None
    """Driver implementation variant name (default provided if missing)."""
    raise_exceptions: bool = False
    """Raise exceptions if True."""
    top_task_label: Text = 'TASK'
    """Label used in help for top level tasks."""
    sub_task_label: Text = 'SUB_TASK'
    """Label used in help for sub-tasks."""
    top_task_dest_name: Text = 'TASK'
    """Top task destination name"""
    supported_global_options: List[Text] = field(default_factory=list)
    """List of global option names to be made available to the user."""
