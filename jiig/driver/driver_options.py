# Copyright (C) 2021-2023, Steven Cooper
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


@dataclass
class DriverOptions:
    """Options governing Jiig driver behavior."""
    raise_exceptions: bool = False
    """Raise exceptions if True."""
    top_task_label: str = 'TASK'
    """Label used in help for top level tasks."""
    sub_task_label: str = 'SUB_TASK'
    """Label used in help for sub-tasks."""
    top_task_dest_name: str = 'TASK'
    """Top task destination name"""
    global_option_names: list[str] = field(default_factory=list)
    """Supported global option names."""
