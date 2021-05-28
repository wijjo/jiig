"""Driver options data class."""

from dataclasses import dataclass
from typing import Text


@dataclass
class DriverOptions:
    """Options governing Jiig driver behavior."""
    variant: Text = None
    """Driver implementation variant name (default provided if missing)."""
    disable_debug: bool = False
    """Disable the debug option."""
    disable_dry_run: bool = False
    """Disable the dry run option."""
    disable_verbose: bool = False
    """Disable the verbose option."""
    enable_pause: bool = False
    """Enable the pause option."""
    raise_exceptions: bool = False
    """Raise exceptions if True."""
    top_task_label: Text = 'TASK'
    """Label used in help for top level tasks."""
    sub_task_label: Text = 'SUB_TASK'
    """Label used in help for sub-tasks."""
    top_task_dest_name: Text = 'TASK'
    """Top task destination name"""
