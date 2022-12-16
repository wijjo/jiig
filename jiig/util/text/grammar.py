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

"""
General-purpose (independent) utilities.

Make sure that any other utility module can import this module without circular
import references. I.e. DO NOT import other utility modules here.

To handle errors independently, avoid functions like console.log_error(), and
either throw an exception or provide an informative return value.
"""

from typing import Any


def pluralize(noun: str, countable: Any):
    """
    Simplistic text pluralization.

    If `countable` length is one:

    - Return unchanged.

    Otherwise if countable length is zero or greater than one:

    - If it ends in 'y', return with ending 'y' replaced by 'ies'.
    - Otherwise return with 's' appended.

    ** No other irregular pluralization cases are handled. Please be aware of
    the input, and how the simplistic algorithm works for it (or not). **

    :param noun: noun to pluralize as needed
    :param countable: item with a length that determines if it is pluralized
    :return: possibly-pluralized noun
    """
    try:
        if len(countable) != 1:
            if noun.endswith('y'):
                return f'{noun[:-1]}ies'
            return f'{noun}s'
    except TypeError:
        pass
    return noun
