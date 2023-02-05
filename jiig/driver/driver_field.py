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

"""Driver field data."""

from typing import Any, Sequence

from ..util.default import DefaultValue
from ..util.repetition import Repetition


class DriverField:
    """Field data fed to driver."""
    def __init__(self,
                 name: str,
                 description: str,
                 element_type: Any,
                 repeat: Repetition = None,
                 default: DefaultValue = None,
                 choices: Sequence = None,
                 ):
        """
        Driver field constructor.

        :param name: field name
        :param description: field description
        :param element_type: field element type
        :param repeat: optional repeat data
        :param default: optional default value
        :param choices: optional permitted values
        """
        self.name = name
        self.description = description
        self.element_type = element_type
        self.repeat = repeat
        self.default = default
        self.choices = choices
