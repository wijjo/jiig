# Copyright (C) 2020-2022, Steven Cooper
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

from .log import log_error
from .types import RepeatSpec, Repetition


def repetition_from_spec(spec: RepeatSpec | None) -> Repetition:
    """
    Convert raw repeat specification to a Repetition object.

    Most of the code is purely sanity checking.

    :param spec: raw integer or pair of optional integers
    :return: Repetition object or None for bad or missing input data
    """
    if spec is None:
        return Repetition(None, None)
    if isinstance(spec, int):
        if spec > 0:
            return Repetition(spec, spec)
    elif isinstance(spec, tuple) and len(spec) == 2:
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
