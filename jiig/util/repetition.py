# Copyright (C) 2020-2023, Steven Cooper
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

"""Repetition specification and data class."""

from dataclasses import dataclass

from .log import log_error

# Raw repetition specification type.
RepeatSpec = int | tuple[int | None, int | None]


@dataclass
class Repetition:
    minimum: int | None
    maximum: int | None


def repetition_from_spec(spec: RepeatSpec | None) -> Repetition:
    """Convert raw repeat specification to a Repetition object.

    Most of the code is purely sanity checking.

    Args:
        spec: raw integer or pair of optional integers

    Returns:
        Repetition object or None for bad or missing input data
    """
    if spec is None:
        return Repetition(None, None)
    if isinstance(spec, int):
        if spec > 0:
            return Repetition(spec, spec)
    elif isinstance(spec, tuple):
        # An empty tuple allows any repetition.
        if len(spec) == 0:
            return Repetition(None, None)
        # A tuple singleton sets the value as both the minimum and maximum.
        if len(spec) == 1:
            return Repetition(spec[0], spec[0])
        # A tuple pair sets the minimum and maximum if they make sense.
        if len(spec) == 2:
            if spec[0] is None:
                if spec[1] is None:
                    return Repetition(None, None)
                if isinstance(spec[1], int) and spec[1] >= 1:
                    return Repetition(spec[0], spec[1])
            elif isinstance(spec[0], int) and spec[0] >= 0:
                if spec[1] is None:
                    return Repetition(spec[0], None)
                if isinstance(spec[1], int) and spec[1] >= spec[0]:
                    return Repetition(spec[0], spec[1])
    log_error(f'Repeat specification {spec} is not one of the following:',
              '- None for non-repeating field.',
              '- A single integer for a specific required quantity.',
              '- A tuple pair to express a range, with None meaning zero or infinity.')
    return Repetition(None, None)
