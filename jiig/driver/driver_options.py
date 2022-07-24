# Copyright (C) 2021-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

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
