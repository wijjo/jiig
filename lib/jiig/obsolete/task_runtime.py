"""
Task runtime data derived from Task configuration.
"""

from dataclasses import dataclass
from typing import Text, List, Optional

from jiig.typing import RunFunction, DoneFunction

from jiig.model.option_data import OptionData
from jiig.model.argument_data import ArgumentData


@dataclass
class TaskRuntime:
    """Task runtime data."""

    name: Text
    """Task name."""

    visibility: int
    """Help visibility - 0=primary, 1=secondary, 2=hidden"""

    opts: List[OptionData]
    """Options specifications."""

    args: List[ArgumentData]
    """Positional argument specifications"""

    sub_tasks: Optional[List['TaskRuntime']]
    """Sub-tasks."""

    receive_trailing_arguments: bool
    """Keep unparsed trailing arguments if True."""

    run_functions: List[RunFunction]
    """Registered @run functions called to execute the task."""

    done_functions: List[DoneFunction]
    """Registered @done functions called when the task completes."""
