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
