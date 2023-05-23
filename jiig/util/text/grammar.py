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

"""General-purpose (independent) utilities.

Make sure that any other utility module can import this module without circular
import references. I.e. DO NOT import other utility modules here.

To handle errors independently, avoid functions like console.log_error(), and
either throw an exception or provide an informative return value.
"""

from typing import Collection


def pluralize(noun: str, countable: Collection = None, count: int = None):
    """Simplistic text pluralization.

    If `countable` length or `count` is 1:

    - Return unchanged.

    If `countable` and `count` is None:

    - Return pluralized (see below).

    Otherwise if countable length is zero or greater than one:

    - If it ends in 'y', return with ending 'y' replaced by 'ies'.
    - If it ends in 's', adds 'es' to pluralize.
    - Otherwise return with 's' appended.

    ** No other irregular pluralization cases are handled. Please be aware of
    the input, and how the simplistic algorithm works for it (or not). **

    Args:
        noun: noun to pluralize as needed
        countable: optional collection with size to determine pluralization
        count: optional count integer to determine pluralization


    Returns:
        possibly-pluralized noun
    """
    try:
        if countable is not None:
            quantity = len(countable)
        elif count is not None:
            quantity = count
        else:
            quantity = 0    # Force plural.
        if quantity != 1:
            if noun.endswith('y'):
                return f'{noun[:-1]}ies'
            if noun.endswith('s'):
                return f'{noun}es'
            return f'{noun}s'
    except TypeError:
        pass
    return noun
